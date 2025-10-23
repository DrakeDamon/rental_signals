{{
  config(
    materialized='table',
    description='Rent vs CPI correlation analysis with inflation impact metrics'
  )
}}

with monthly_rent_data as (
    select
        t.month_date,
        t.year,
        t.quarter,
        
        -- National rent averages from Zillow
        avg(case when l.location_type = 'metro' then fz.zori_value end) as national_avg_zori,
        avg(case when l.location_type = 'metro' then fz.yoy_pct_change end) as national_rent_yoy,
        median(case when l.location_type = 'metro' then fz.zori_value end) as national_median_zori,
        
        -- Population-weighted averages
        sum(case when l.location_type = 'metro' then fz.zori_value * l.population end) / 
        nullif(sum(case when l.location_type = 'metro' then l.population end), 0) as population_weighted_zori,
        
        -- Market counts and quality indicators
        count(distinct case when l.location_type = 'metro' then l.location_key end) as metro_count,
        avg(fz.data_quality_score) as avg_data_quality,
        sum(case when fz.has_anomaly then 1 else 0 end) as anomaly_count
        
    from {{ ref('fact_rent_zori') }} fz
    join {{ ref('dim_location') }} l on fz.location_key = l.location_key
    join {{ ref('dim_time') }} t on fz.time_key = t.time_key
    group by t.month_date, t.year, t.quarter
),

monthly_cpi_data as (
    select
        t.month_date,
        t.year,
        t.quarter,
        
        -- CPI indicators by category
        avg(case when es.category = 'Housing CPI' then fei.indicator_value end) as housing_cpi,
        avg(case when es.category = 'All Items CPI' then fei.indicator_value end) as all_items_cpi,
        avg(case when es.category = 'Core CPI' then fei.indicator_value end) as core_cpi,
        
        -- CPI year-over-year changes
        avg(case when es.category = 'Housing CPI' then fei.yoy_pct_change end) as housing_cpi_yoy,
        avg(case when es.category = 'All Items CPI' then fei.yoy_pct_change end) as all_items_cpi_yoy,
        avg(case when es.category = 'Core CPI' then fei.yoy_pct_change end) as core_cpi_yoy,
        
        -- CPI month-over-month changes
        avg(case when es.category = 'Housing CPI' then fei.mom_pct_change end) as housing_cpi_mom,
        avg(case when es.category = 'All Items CPI' then fei.mom_pct_change end) as all_items_cpi_mom
        
    from {{ ref('fact_economic_indicator') }} fei
    join {{ ref('dim_economic_series') }} es on fei.series_key = es.series_key
    join {{ ref('dim_time') }} t on fei.time_key = t.time_key
    group by t.month_date, t.year, t.quarter
),

combined_data as (
    select
        coalesce(r.month_date, c.month_date) as month_date,
        coalesce(r.year, c.year) as year,
        coalesce(r.quarter, c.quarter) as quarter,
        
        -- Rent metrics
        r.national_avg_zori,
        r.national_rent_yoy,
        r.national_median_zori,
        r.population_weighted_zori,
        r.metro_count,
        r.avg_data_quality,
        r.anomaly_count,
        
        -- CPI metrics
        c.housing_cpi,
        c.all_items_cpi,
        c.core_cpi,
        c.housing_cpi_yoy,
        c.all_items_cpi_yoy,
        c.core_cpi_yoy,
        c.housing_cpi_mom,
        c.all_items_cpi_mom
        
    from monthly_rent_data r
    full outer join monthly_cpi_data c on r.month_date = c.month_date
    where coalesce(r.month_date, c.month_date) >= '2015-01-01'
),

correlation_analysis as (
    select
        *,
        
        -- Calculate spreads (rent vs inflation)
        national_rent_yoy - housing_cpi_yoy as rent_housing_cpi_spread,
        national_rent_yoy - all_items_cpi_yoy as rent_general_inflation_spread,
        national_rent_yoy - core_cpi_yoy as rent_core_cpi_spread,
        
        -- Rolling averages for smoothing
        avg(national_rent_yoy) over (
            order by month_date 
            rows between 11 preceding and current row
        ) as rent_yoy_12m_avg,
        
        avg(housing_cpi_yoy) over (
            order by month_date 
            rows between 11 preceding and current row
        ) as housing_cpi_12m_avg,
        
        avg(all_items_cpi_yoy) over (
            order by month_date 
            rows between 11 preceding and current row
        ) as all_items_cpi_12m_avg,
        
        -- Volatility measures
        stddev(national_rent_yoy) over (
            order by month_date 
            rows between 11 preceding and current row
        ) as rent_yoy_volatility,
        
        stddev(housing_cpi_yoy) over (
            order by month_date 
            rows between 11 preceding and current row
        ) as housing_cpi_volatility,
        
        -- Correlation indicators
        case 
            when abs(national_rent_yoy - housing_cpi_yoy) <= 2 then 'Aligned'
            when national_rent_yoy > housing_cpi_yoy + 2 then 'Rent Outpacing Housing CPI'
            when all_items_cpi_yoy > national_rent_yoy + 2 then 'General Inflation Outpacing Rent'
            else 'Mixed Relationship'
        end as correlation_status
        
    from combined_data
),

final_metrics as (
    select
        *,
        
        -- Economic regime classification
        case
            when all_items_cpi_yoy > 5 and national_rent_yoy > 10 then 'High Inflation + Hot Rent Market'
            when all_items_cpi_yoy > 3 and national_rent_yoy > 5 then 'Moderate Inflation + Growing Rents'
            when all_items_cpi_yoy < 2 and national_rent_yoy < 3 then 'Low Inflation + Stable Rents'
            when all_items_cpi_yoy > 3 and national_rent_yoy < 0 then 'Stagflation Risk'
            when all_items_cpi_yoy < 0 and national_rent_yoy < 0 then 'Deflationary Pressure'
            else 'Transitional Period'
        end as economic_regime,
        
        -- Rent affordability pressure
        case
            when rent_general_inflation_spread > 5 then 'Severe Affordability Crisis'
            when rent_general_inflation_spread > 2 then 'Affordability Pressure'
            when rent_general_inflation_spread between -1 and 2 then 'Balanced'
            when rent_general_inflation_spread < -3 then 'Improving Affordability'
            else 'Stable Affordability'
        end as affordability_pressure,
        
        -- Policy implications
        case
            when rent_housing_cpi_spread > 3 and housing_cpi_yoy > 3 then 'Consider Rent Controls'
            when rent_general_inflation_spread > 5 then 'Housing Supply Crisis'
            when national_rent_yoy < 0 and all_items_cpi_yoy > 2 then 'Economic Divergence'
            when abs(rent_housing_cpi_spread) <= 1 then 'Market Equilibrium'
            else 'Monitor Trends'
        end as policy_implications,
        
        -- Load metadata
        current_timestamp() as mart_created_at,
        '{{ run_started_at }}' as dbt_run_id
        
    from correlation_analysis
)

select * from final_metrics
where month_date is not null
order by month_date