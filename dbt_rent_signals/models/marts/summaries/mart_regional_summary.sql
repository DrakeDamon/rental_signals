{{
  config(
    materialized='table',
    description='State and national level aggregations with market characterization'
  )
}}

with latest_month as (
    select max(time_key) as latest_time_key 
    from {{ ref('dim_time') }}
    where month_date <= current_date()
),

state_level_data as (
    select
        'State' as aggregation_level,
        l.state_name as region_name,
        l.state_name,
        
        -- Counts and totals
        count(distinct l.location_key) as location_count,
        sum(l.population) as total_population,
        
        -- Rent statistics
        avg(fz.zori_value) as avg_zori,
        median(fz.zori_value) as median_zori,
        min(fz.zori_value) as min_zori,
        max(fz.zori_value) as max_zori,
        stddev(fz.zori_value) as zori_stddev,
        
        -- Growth statistics  
        avg(fz.yoy_pct_change) as avg_yoy_growth,
        median(fz.yoy_pct_change) as median_yoy_growth,
        min(fz.yoy_pct_change) as min_yoy_growth,
        max(fz.yoy_pct_change) as max_yoy_growth,
        stddev(fz.yoy_pct_change) as yoy_growth_stddev,
        
        -- Market condition counts
        count(case when fz.yoy_pct_change > 10 then 1 end) as very_hot_markets,
        count(case when fz.yoy_pct_change between 5 and 10 then 1 end) as hot_markets,
        count(case when fz.yoy_pct_change between 0 and 5 then 1 end) as growing_markets,
        count(case when fz.yoy_pct_change between -5 and 0 then 1 end) as cooling_markets,
        count(case when fz.yoy_pct_change < -5 then 1 end) as declining_markets,
        
        -- Data quality indicators
        avg(fz.data_quality_score) as avg_data_quality,
        count(case when fz.has_anomaly then 1 end) as anomaly_count,
        
        -- Size distribution
        count(case when l.market_size_category = 'Major Metro (5M+)' then 1 end) as major_metros,
        count(case when l.market_size_category = 'Large Metro (1M-5M)' then 1 end) as large_metros,
        count(case when l.market_size_category = 'Medium Metro (250K-1M)' then 1 end) as medium_metros,
        count(case when l.market_size_category = 'Small Metro (<250K)' then 1 end) as small_metros
        
    from {{ ref('fact_rent_zori') }} fz
    join {{ ref('dim_location') }} l on fz.location_key = l.location_key
    join latest_month lm on fz.time_key = lm.latest_time_key
    where l.state_name is not null
    group by l.state_name
),

national_level_data as (
    select
        'National' as aggregation_level,
        'United States' as region_name,
        'US' as state_name,
        
        -- Counts and totals
        count(distinct l.location_key) as location_count,
        sum(l.population) as total_population,
        
        -- Rent statistics
        avg(fz.zori_value) as avg_zori,
        median(fz.zori_value) as median_zori,
        min(fz.zori_value) as min_zori,
        max(fz.zori_value) as max_zori,
        stddev(fz.zori_value) as zori_stddev,
        
        -- Growth statistics
        avg(fz.yoy_pct_change) as avg_yoy_growth,
        median(fz.yoy_pct_change) as median_yoy_growth,
        min(fz.yoy_pct_change) as min_yoy_growth,
        max(fz.yoy_pct_change) as max_yoy_growth,
        stddev(fz.yoy_pct_change) as yoy_growth_stddev,
        
        -- Market condition counts
        count(case when fz.yoy_pct_change > 10 then 1 end) as very_hot_markets,
        count(case when fz.yoy_pct_change between 5 and 10 then 1 end) as hot_markets,
        count(case when fz.yoy_pct_change between 0 and 5 then 1 end) as growing_markets,
        count(case when fz.yoy_pct_change between -5 and 0 then 1 end) as cooling_markets,
        count(case when fz.yoy_pct_change < -5 then 1 end) as declining_markets,
        
        -- Data quality indicators
        avg(fz.data_quality_score) as avg_data_quality,
        count(case when fz.has_anomaly then 1 end) as anomaly_count,
        
        -- Size distribution
        count(case when l.market_size_category = 'Major Metro (5M+)' then 1 end) as major_metros,
        count(case when l.market_size_category = 'Large Metro (1M-5M)' then 1 end) as large_metros,
        count(case when l.market_size_category = 'Medium Metro (250K-1M)' then 1 end) as medium_metros,
        count(case when l.market_size_category = 'Small Metro (<250K)' then 1 end) as small_metros
        
    from {{ ref('fact_rent_zori') }} fz
    join {{ ref('dim_location') }} l on fz.location_key = l.location_key
    join latest_month lm on fz.time_key = lm.latest_time_key
),

combined_summaries as (
    select * from state_level_data
    union all
    select * from national_level_data
),

enhanced_summaries as (
    select
        *,
        
        -- Add rankings within aggregation level
        rank() over (partition by aggregation_level order by avg_zori desc) as rent_rank,
        rank() over (partition by aggregation_level order by avg_yoy_growth desc) as growth_rank,
        rank() over (partition by aggregation_level order by total_population desc) as population_rank,
        
        -- Calculate percentage distributions
        round(very_hot_markets::float / nullif(location_count, 0) * 100, 1) as pct_very_hot_markets,
        round(hot_markets::float / nullif(location_count, 0) * 100, 1) as pct_hot_markets,
        round(growing_markets::float / nullif(location_count, 0) * 100, 1) as pct_growing_markets,
        round(cooling_markets::float / nullif(location_count, 0) * 100, 1) as pct_cooling_markets,
        round(declining_markets::float / nullif(location_count, 0) * 100, 1) as pct_declining_markets,
        
        -- Market characterization
        case 
            when avg_yoy_growth > 12 then 'Overheating'
            when avg_yoy_growth > 8 then 'Very Hot'
            when avg_yoy_growth > 5 then 'Hot'
            when avg_yoy_growth > 2 then 'Warm'
            when avg_yoy_growth > 0 then 'Cool'
            when avg_yoy_growth > -3 then 'Cold'
            else 'Frozen'
        end as market_temperature,
        
        -- Stability assessment
        case
            when yoy_growth_stddev < 3 then 'Very Stable'
            when yoy_growth_stddev < 5 then 'Stable'
            when yoy_growth_stddev < 8 then 'Moderate Volatility'
            when yoy_growth_stddev < 12 then 'High Volatility'
            else 'Extreme Volatility'
        end as market_stability,
        
        -- Diversity score (based on size distribution)
        case
            when major_metros > 0 and large_metros > 0 and medium_metros > 0 then 'Highly Diverse'
            when (major_metros > 0 and large_metros > 0) or (large_metros > 0 and medium_metros > 0) then 'Moderately Diverse'
            when major_metros + large_metros + medium_metros > 0 then 'Somewhat Diverse'
            else 'Limited Diversity'
        end as market_diversity,
        
        -- Affordability classification
        case
            when avg_zori > 3000 then 'Very Expensive'
            when avg_zori > 2500 then 'Expensive'
            when avg_zori > 2000 then 'Moderately Expensive'
            when avg_zori > 1500 then 'Moderate'
            when avg_zori > 1000 then 'Affordable'
            else 'Very Affordable'
        end as affordability_classification,
        
        -- Population-weighted average rent
        case
            when total_population > 0 then 
                (select sum(fz.zori_value * l.population) / sum(l.population)
                 from {{ ref('fact_rent_zori') }} fz
                 join {{ ref('dim_location') }} l on fz.location_key = l.location_key
                 join latest_month lm on fz.time_key = lm.latest_time_key
                 where (combined_summaries.aggregation_level = 'National') or 
                       (combined_summaries.aggregation_level = 'State' and l.state_name = combined_summaries.state_name))
            else null
        end as population_weighted_avg_rent,
        
        -- Load metadata
        current_timestamp() as mart_created_at,
        '{{ run_started_at }}' as dbt_run_id
        
    from combined_summaries
)

select * from enhanced_summaries
order by 
    case aggregation_level when 'National' then 1 else 2 end,
    avg_yoy_growth desc