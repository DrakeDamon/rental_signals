{{
  config(
    materialized='table',
    description='Market competitiveness rankings with heat scores and investment metrics'
  )
}}

with latest_month as (
    select max(time_key) as latest_time_key 
    from {{ ref('dim_time') }}
    where month_date <= current_date()
),

zori_latest as (
    select
        fz.*,
        l.location_name,
        l.state_name,
        l.metro_name,
        l.population,
        l.market_size_category
    from {{ ref('fact_rent_zori') }} fz
    join {{ ref('dim_location') }} l on fz.location_key = l.location_key
    join latest_month lm on fz.time_key = lm.latest_time_key
),

market_metrics as (
    select
        location_name,
        state_name,
        metro_name,
        population,
        market_size_category,
        zori_value,
        yoy_pct_change,
        mom_pct_change,
        size_rank,
        data_quality_score,
        has_anomaly,
        
        -- Calculate percentiles for scoring
        percent_rank() over (order by zori_value) as rent_percentile,
        percent_rank() over (order by yoy_pct_change) as growth_percentile,
        percent_rank() over (order by population) as population_percentile,
        percent_rank() over (order by data_quality_score) as quality_percentile,
        
        -- Rankings
        rank() over (order by zori_value desc) as rent_rank,
        rank() over (order by yoy_pct_change desc) as growth_rank,
        rank() over (order by population desc) as population_rank,
        
        -- Calculate moving averages for stability
        avg(zori_value) over (
            partition by regionid 
            order by month_date 
            rows between 11 preceding and current row
        ) as twelve_month_avg_rent,
        
        stddev(zori_value) over (
            partition by regionid 
            order by month_date 
            rows between 11 preceding and current row
        ) as twelve_month_rent_volatility
        
    from zori_latest
),

market_scoring as (
    select
        *,
        
        -- Composite market heat score (0-100)
        round(
            (rent_percentile * 30) +           -- 30% weight to absolute rent level
            (growth_percentile * 40) +         -- 40% weight to growth rate
            (population_percentile * 20) +     -- 20% weight to market size
            (quality_percentile * 10),         -- 10% weight to data quality
            1
        ) * 100 as market_heat_score,
        
        -- Investment potential score (adjusted for risk)
        round(
            (growth_percentile * 50) +         -- Heavy weight on growth
            (population_percentile * 25) +     -- Market size importance
            (quality_percentile * 15) +        -- Data reliability
            ((1 - rent_percentile) * 10) -     -- Bonus for lower absolute rents (better value)
            (case when has_anomaly then 20 else 0 end), -- Penalty for data anomalies
            1
        ) * 100 as investment_potential_score,
        
        -- Stability score (lower volatility = higher score)
        case
            when twelve_month_rent_volatility is null then null
            else round(
                100 - (twelve_month_rent_volatility / twelve_month_avg_rent * 100),
                1
            )
        end as market_stability_score
        
    from market_metrics
),

market_classification as (
    select
        *,
        
        -- Market classification based on heat score
        case 
            when market_heat_score >= 80 then 'Superstar Market'
            when market_heat_score >= 65 then 'Hot Market'
            when market_heat_score >= 50 then 'Growing Market'
            when market_heat_score >= 35 then 'Stable Market'
            when market_heat_score >= 20 then 'Cool Market'
            else 'Struggling Market'
        end as market_classification,
        
        -- Investment recommendation
        case
            when investment_potential_score >= 75 and market_stability_score >= 60 then 'Strong Buy'
            when investment_potential_score >= 60 and market_stability_score >= 50 then 'Buy'
            when investment_potential_score >= 45 or market_stability_score >= 70 then 'Hold'
            when investment_potential_score >= 30 then 'Caution'
            else 'Avoid'
        end as investment_recommendation,
        
        -- Risk assessment
        case
            when has_anomaly then 'High Risk - Data Anomaly'
            when market_stability_score < 30 then 'High Risk - Volatile'
            when data_quality_score < 7 then 'Medium Risk - Data Quality'
            when yoy_pct_change < -10 then 'Medium Risk - Declining'
            when market_stability_score >= 60 and data_quality_score >= 8 then 'Low Risk'
            else 'Medium Risk'
        end as risk_assessment,
        
        -- Trend momentum
        case
            when yoy_pct_change > 10 and mom_pct_change > 1 then 'Strong Upward'
            when yoy_pct_change > 5 and mom_pct_change > 0 then 'Moderate Upward'
            when yoy_pct_change > 0 and mom_pct_change between -1 and 1 then 'Stable Growth'
            when yoy_pct_change between -5 and 0 then 'Cooling'
            when yoy_pct_change < -5 and mom_pct_change < -1 then 'Strong Downward'
            else 'Mixed Signals'
        end as trend_momentum,
        
        -- Load metadata
        current_timestamp() as mart_created_at,
        '{{ run_started_at }}' as dbt_run_id
        
    from market_scoring
)

select * from market_classification
order by market_heat_score desc, investment_potential_score desc