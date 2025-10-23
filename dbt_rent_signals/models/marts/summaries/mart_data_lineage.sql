{{
  config(
    materialized='table',
    description='Data quality monitoring and source system tracking for operational insights'
  )
}}

with zori_lineage as (
    select
        'FACT_RENT_ZORI' as table_name,
        ds.source_name,
        ds.source_system,
        count(*) as record_count,
        max(fz.month_date) as latest_data_date,
        max(fz.load_date) as latest_load_date,
        min(fz.data_quality_score) as min_quality_score,
        avg(fz.data_quality_score) as avg_quality_score,
        max(fz.data_quality_score) as max_quality_score,
        count(case when fz.has_anomaly then 1 end) as anomaly_count,
        count(distinct fz.time_key) as unique_months,
        count(distinct fz.location_key) as unique_locations,
        
        -- Additional metrics
        min(fz.zori_value) as min_value,
        avg(fz.zori_value) as avg_value,
        max(fz.zori_value) as max_value,
        stddev(fz.zori_value) as value_stddev,
        
        -- Growth metrics
        avg(fz.yoy_pct_change) as avg_yoy_growth,
        min(fz.yoy_pct_change) as min_yoy_growth,
        max(fz.yoy_pct_change) as max_yoy_growth,
        
        -- Data range
        min(fz.month_date) as earliest_data_date,
        count(distinct extract(year from fz.month_date)) as years_of_data
        
    from {{ ref('fact_rent_zori') }} fz
    join {{ ref('dim_data_source') }} ds on fz.source_key = ds.source_key
    group by ds.source_name, ds.source_system
),

aptlist_lineage as (
    select
        'FACT_RENT_APTLIST' as table_name,
        ds.source_name,
        ds.source_system,
        count(*) as record_count,
        max(fa.month_date) as latest_data_date,
        max(fa.load_date) as latest_load_date,
        min(fa.data_quality_score) as min_quality_score,
        avg(fa.data_quality_score) as avg_quality_score,
        max(fa.data_quality_score) as max_quality_score,
        count(case when fa.has_anomaly then 1 end) as anomaly_count,
        count(distinct fa.time_key) as unique_months,
        count(distinct fa.location_key) as unique_locations,
        
        -- Additional metrics
        min(fa.rent_index) as min_value,
        avg(fa.rent_index) as avg_value,
        max(fa.rent_index) as max_value,
        stddev(fa.rent_index) as value_stddev,
        
        -- Growth metrics
        avg(fa.yoy_pct_change) as avg_yoy_growth,
        min(fa.yoy_pct_change) as min_yoy_growth,
        max(fa.yoy_pct_change) as max_yoy_growth,
        
        -- Data range
        min(fa.month_date) as earliest_data_date,
        count(distinct extract(year from fa.month_date)) as years_of_data
        
    from {{ ref('fact_rent_aptlist') }} fa
    join {{ ref('dim_data_source') }} ds on fa.source_key = ds.source_key
    group by ds.source_name, ds.source_system
),

economic_lineage as (
    select
        'FACT_ECONOMIC_INDICATOR' as table_name,
        ds.source_name,
        ds.source_system,
        count(*) as record_count,
        max(fei.month_date) as latest_data_date,
        max(fei.load_date) as latest_load_date,
        min(fei.data_quality_score) as min_quality_score,
        avg(fei.data_quality_score) as avg_quality_score,
        max(fei.data_quality_score) as max_quality_score,
        0 as anomaly_count,  -- Economic indicators don't have anomaly detection in current model
        count(distinct fei.time_key) as unique_months,
        count(distinct fei.series_key) as unique_locations,  -- Series instead of locations
        
        -- Additional metrics
        min(fei.indicator_value) as min_value,
        avg(fei.indicator_value) as avg_value,
        max(fei.indicator_value) as max_value,
        stddev(fei.indicator_value) as value_stddev,
        
        -- Growth metrics
        avg(fei.yoy_pct_change) as avg_yoy_growth,
        min(fei.yoy_pct_change) as min_yoy_growth,
        max(fei.yoy_pct_change) as max_yoy_growth,
        
        -- Data range
        min(fei.month_date) as earliest_data_date,
        count(distinct extract(year from fei.month_date)) as years_of_data
        
    from {{ ref('fact_economic_indicator') }} fei
    join {{ ref('dim_data_source') }} ds on fei.source_key = ds.source_key
    group by ds.source_name, ds.source_system
),

combined_lineage as (
    select * from zori_lineage
    union all
    select * from aptlist_lineage  
    union all
    select * from economic_lineage
),

enhanced_lineage as (
    select
        *,
        
        -- Data freshness calculations
        datediff('day', latest_data_date, current_date()) as days_since_latest_data,
        datediff('hour', latest_load_date, current_timestamp()) as hours_since_latest_load,
        
        -- Data freshness status
        case 
            when datediff('day', latest_data_date, current_date()) <= 45 then 'Fresh'
            when datediff('day', latest_data_date, current_date()) <= 90 then 'Stale'
            else 'Very Stale'
        end as data_freshness_status,
        
        -- Data quality status
        case 
            when avg_quality_score >= 9 then 'Excellent'
            when avg_quality_score >= 7 then 'Good'
            when avg_quality_score >= 5 then 'Fair'
            else 'Poor'
        end as data_quality_status,
        
        -- Anomaly percentage
        round(anomaly_count::float / nullif(record_count, 0) * 100, 2) as anomaly_percentage,
        
        -- Completeness metrics
        case
            when table_name = 'FACT_RENT_ZORI' then 
                record_count::float / nullif(unique_months * unique_locations, 0)
            when table_name = 'FACT_RENT_APTLIST' then 
                record_count::float / nullif(unique_months * unique_locations, 0)
            else 
                record_count::float / nullif(unique_months * unique_locations, 0)
        end as completeness_ratio,
        
        -- Data volume trend (simple approximation)
        case
            when years_of_data > 0 then record_count::float / years_of_data
            else null
        end as avg_records_per_year,
        
        -- Data coverage assessment
        case
            when unique_months >= 60 then 'Excellent Coverage (5+ years)'
            when unique_months >= 36 then 'Good Coverage (3-5 years)'
            when unique_months >= 12 then 'Fair Coverage (1-3 years)'
            else 'Limited Coverage (<1 year)'
        end as temporal_coverage,
        
        -- Geographic coverage (for rent data)
        case
            when table_name like '%RENT%' and unique_locations >= 100 then 'National Coverage'
            when table_name like '%RENT%' and unique_locations >= 50 then 'Regional Coverage'
            when table_name like '%RENT%' and unique_locations >= 10 then 'Limited Coverage'
            when table_name like '%RENT%' then 'Minimal Coverage'
            else 'Economic Series'
        end as geographic_coverage,
        
        -- Reliability score based on multiple factors
        least(100, greatest(0,
            (avg_quality_score * 10) +  -- Base quality score
            (case when data_freshness_status = 'Fresh' then 20 when data_freshness_status = 'Stale' then 10 else 0 end) +  -- Freshness bonus
            (case when years_of_data >= 5 then 15 when years_of_data >= 3 then 10 when years_of_data >= 1 then 5 else 0 end) +  -- History bonus
            (case when anomaly_percentage < 1 then 10 when anomaly_percentage < 5 then 5 else 0 end) -  -- Anomaly penalty
            (case when completeness_ratio < 0.8 then 20 when completeness_ratio < 0.9 then 10 else 0 end)  -- Completeness penalty
        )) as overall_reliability_score,
        
        -- Load metadata
        current_timestamp() as mart_created_at,
        '{{ run_started_at }}' as dbt_run_id
        
    from combined_lineage
)

select * from enhanced_lineage
order by table_name, source_name