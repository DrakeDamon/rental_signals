{{
  config(
    materialized='table',
    description='Zillow ZORI rent facts with calculated measures and data quality scoring'
  )
}}

with staging_data as (
    select * from {{ ref('stg_zori') }}
),

time_dim as (
    select * from {{ ref('dim_time') }}
),

location_dim as (
    select * from {{ ref('dim_location') }}
    where is_current = true
),

data_source_dim as (
    select * from {{ ref('dim_data_source') }}
    where source_name = 'Zillow ZORI'
),

fact_data as (
    select
        -- Dimension foreign keys
        t.time_key,
        l.location_key,
        ds.source_key,
        
        -- Business keys for debugging
        s.regionid,
        s.month_date,
        
        -- Measures
        s.zori_value,
        s.size_rank,
        
        -- Calculate year-over-year and month-over-month changes
        {{ calculate_changes('s.zori_value', 's.regionid') }},
        
        -- Record count (always 1 for grain validation)
        1 as record_count,
        
        -- Enhanced data quality scoring
        {{ data_quality_score(
            value_column='s.zori_value',
            min_value=0,
            max_value=15000,
            required_columns=['s.regionid', 's.location_name']
        ) }} as data_quality_score,
        
        -- Enhanced anomaly detection
        {{ detect_anomalies(
            value_column='s.zori_value',
            partition_by='s.regionid',
            window_size=6,
            std_dev_threshold=2.5
        ) }} as has_anomaly,
        
        -- Additional calculated measures
        s.zori_value / nullif(l.population, 0) * 1000 as zori_per_1k_residents,
        
        -- Ranking measures
        rank() over (
            partition by s.month_date 
            order by s.zori_value desc
        ) as national_rank,
        
        rank() over (
            partition by s.month_date, l.state_name 
            order by s.zori_value desc
        ) as state_rank,
        
        -- Percentile measures
        percent_rank() over (
            partition by s.month_date 
            order by s.zori_value
        ) as national_percentile,
        
        -- Trend categorization
        case 
            when lag(s.zori_value, 12) over (
                partition by s.regionid 
                order by s.month_date
            ) is null then 'Insufficient History'
            when (s.zori_value - lag(s.zori_value, 12) over (
                partition by s.regionid 
                order by s.month_date
            )) / nullif(lag(s.zori_value, 12) over (
                partition by s.regionid 
                order by s.month_date
            ), 0) * 100 > 10 then 'High Growth'
            when (s.zori_value - lag(s.zori_value, 12) over (
                partition by s.regionid 
                order by s.month_date
            )) / nullif(lag(s.zori_value, 12) over (
                partition by s.regionid 
                order by s.month_date
            ), 0) * 100 > 5 then 'Moderate Growth'
            when (s.zori_value - lag(s.zori_value, 12) over (
                partition by s.regionid 
                order by s.month_date
            )) / nullif(lag(s.zori_value, 12) over (
                partition by s.regionid 
                order by s.month_date
            ), 0) * 100 > 0 then 'Low Growth'
            when (s.zori_value - lag(s.zori_value, 12) over (
                partition by s.regionid 
                order by s.month_date
            )) / nullif(lag(s.zori_value, 12) over (
                partition by s.regionid 
                order by s.month_date
            ), 0) * 100 > -5 then 'Slight Decline'
            else 'Significant Decline'
        end as growth_category,
        
        -- Data lineage
        current_timestamp() as load_date,
        'zori_metro_long.csv' as source_file_name,
        s.processed_at,
        s.dbt_run_id
        
    from staging_data s
    inner join time_dim t on 
        year(s.month_date) * 100 + month(s.month_date) = t.time_key
    inner join location_dim l on 
        s.regionid = l.regionid
    cross join data_source_dim ds
)

select * from fact_data