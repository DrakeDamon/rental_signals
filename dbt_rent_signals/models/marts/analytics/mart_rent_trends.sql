{{
  config(
    materialized='table',
    description='Business-ready rent trend analysis combining all data sources with unified metrics'
  )
}}

with zori_data as (
    select
        fz.time_key,
        fz.month_date,
        l.location_name,
        l.location_type,
        l.state_name,
        l.metro_name,
        l.market_size_category,
        'Zillow ZORI' as data_source,
        fz.zori_value as rent_value,
        fz.yoy_change,
        fz.yoy_pct_change,
        fz.mom_change,
        fz.mom_pct_change,
        fz.size_rank,
        l.population,
        fz.data_quality_score,
        fz.has_anomaly,
        'Absolute Dollar Amount' as value_type,
        fz.growth_category,
        fz.national_rank,
        fz.state_rank,
        fz.national_percentile
    from {{ ref('fact_rent_zori') }} fz
    join {{ ref('dim_location') }} l on fz.location_key = l.location_key
    join {{ ref('dim_time') }} t on fz.time_key = t.time_key
),

aptlist_data as (
    select
        fa.time_key,
        fa.month_date,
        l.location_name,
        l.location_type,
        l.state_name,
        l.metro_name,
        l.market_size_category,
        'ApartmentList' as data_source,
        fa.rent_index as rent_value,
        fa.yoy_change,
        fa.yoy_pct_change,
        fa.mom_change,
        fa.mom_pct_change,
        null as size_rank,
        fa.population,
        fa.data_quality_score,
        fa.has_anomaly,
        'Index Value' as value_type,
        fa.growth_category,
        fa.national_rank,
        fa.state_rank,
        fa.national_percentile
    from {{ ref('fact_rent_aptlist') }} fa
    join {{ ref('dim_location') }} l on fa.location_key = l.location_key
    join {{ ref('dim_time') }} t on fa.time_key = t.time_key
),

combined_trends as (
    select * from zori_data
    union all
    select * from aptlist_data
),

enhanced_trends as (
    select
        *,
        
        -- Time-based attributes
        year(month_date) as year,
        quarter(month_date) as quarter,
        month(month_date) as month_number,
        monthname(month_date) as month_name,
        
        -- Enhanced market classification
        case 
            when yoy_pct_change > 15 then 'Very Hot'
            when yoy_pct_change > 10 then 'Hot'
            when yoy_pct_change > 5 then 'Warm'
            when yoy_pct_change > 0 then 'Cool'
            when yoy_pct_change > -5 then 'Cold'
            else 'Frozen'
        end as market_temperature,
        
        -- Rent affordability indicators
        case 
            when rent_value > 2500 then 'Very Expensive'
            when rent_value > 2000 then 'Expensive'
            when rent_value > 1500 then 'Moderate'
            when rent_value > 1000 then 'Affordable'
            else 'Very Affordable'
        end as affordability_category,
        
        -- Volatility classification based on recent changes
        case
            when abs(mom_pct_change) > 5 then 'High Volatility'
            when abs(mom_pct_change) > 2 then 'Medium Volatility'
            else 'Low Volatility'
        end as volatility_category,
        
        -- Investment attractiveness score (0-100)
        case
            when yoy_pct_change is null or population is null then null
            else greatest(0, least(100, 
                50 + -- Base score
                (yoy_pct_change * 2) + -- Growth component (higher = better)
                (case when population > 1000000 then 20 when population > 250000 then 10 else 0 end) + -- Size bonus
                (case when data_quality_score >= 9 then 10 when data_quality_score >= 7 then 5 else 0 end) - -- Quality bonus
                (case when has_anomaly then 15 else 0 end) -- Anomaly penalty
            ))
        end as investment_attractiveness_score,
        
        -- Days since data point
        datediff('day', month_date, current_date()) as days_since_data,
        
        -- Data freshness flag
        case 
            when datediff('day', month_date, current_date()) <= 45 then 'Fresh'
            when datediff('day', month_date, current_date()) <= 90 then 'Stale'
            else 'Very Stale'
        end as data_freshness,
        
        -- Load metadata
        current_timestamp() as mart_created_at,
        '{{ run_started_at }}' as dbt_run_id
        
    from combined_trends
)

select * from enhanced_trends
order by data_source, state_name, location_name, month_date