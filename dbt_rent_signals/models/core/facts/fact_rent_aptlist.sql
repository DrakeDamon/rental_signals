{{
  config(
    materialized='table',
    description='ApartmentList rent facts with calculated measures and data quality scoring'
  )
}}

with staging_data as (
    select * from {{ ref('stg_aptlist') }}
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
    where source_name = 'ApartmentList'
),

fact_data as (
    select
        -- Dimension foreign keys
        t.time_key,
        l.location_key,
        ds.source_key,
        
        -- Business keys for debugging
        s.location_fips_code,
        s.month_date,
        
        -- Measures
        s.rent_index,
        s.population,
        
        -- Calculate year-over-year and month-over-month changes
        {{ calculate_changes('s.rent_index', 's.location_fips_code') }},
        
        -- Record count (always 1 for grain validation)
        1 as record_count,
        
        -- Enhanced data quality scoring
        {{ data_quality_score(
            value_column='s.rent_index',
            min_value=0,
            max_value=2000,
            required_columns=['s.location_fips_code', 's.location_name']
        ) }} as data_quality_score,
        
        -- Enhanced anomaly detection
        {{ detect_anomalies(
            value_column='s.rent_index',
            partition_by='s.location_fips_code',
            window_size=6,
            std_dev_threshold=2.0
        ) }} as has_anomaly,
        
        -- Additional calculated measures
        s.rent_index / nullif(s.population, 0) * 1000 as rent_per_1k_residents,
        
        -- Population density estimation (rough)
        case 
            when s.location_type = 'metro' and s.population > 0 then s.population / 1000.0  -- Assume 1000 sq miles avg for metro
            else null
        end as estimated_population_density,
        
        -- Ranking measures
        rank() over (
            partition by t.time_key 
            order by s.rent_index desc
        ) as national_rank,
        
        rank() over (
            partition by t.time_key, s.state_name 
            order by s.rent_index desc
        ) as state_rank,
        
        -- Percentile measures
        percent_rank() over (
            partition by t.time_key 
            order by s.rent_index
        ) as national_percentile,
        
        -- Trend categorization based on YoY change
        case 
            when lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            ) is null then 'Insufficient History'
            when (s.rent_index - lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            )) / nullif(lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            ), 0) * 100 > 15 then 'Very High Growth'
            when (s.rent_index - lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            )) / nullif(lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            ), 0) * 100 > 8 then 'High Growth'
            when (s.rent_index - lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            )) / nullif(lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            ), 0) * 100 > 3 then 'Moderate Growth'
            when (s.rent_index - lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            )) / nullif(lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            ), 0) * 100 > 0 then 'Low Growth'
            when (s.rent_index - lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            )) / nullif(lag(s.rent_index, 12) over (
                partition by s.location_fips_code 
                order by s.month_date
            ), 0) * 100 > -3 then 'Slight Decline'
            else 'Significant Decline'
        end as growth_category,
        
        -- Market classification
        case
            when s.location_type = 'metro' and s.population >= 1000000 then 'Major Metro'
            when s.location_type = 'metro' and s.population >= 250000 then 'Mid-Size Metro'
            when s.location_type = 'metro' then 'Small Metro'
            when s.location_type = 'county' then 'County'
            else s.location_type
        end as market_classification,
        
        -- Data lineage
        current_timestamp() as load_date,
        'apartmentlist_long.csv' as source_file_name,
        s.processed_at,
        s.dbt_run_id
        
    from staging_data s
    inner join time_dim t on 
        (year(s.month_date) * 100 + month(s.month_date)) = t.time_key
    inner join location_dim l on 
        coalesce(s.location_fips_code, 'UNKNOWN') = coalesce(l.location_fips_code, 'UNKNOWN')
    cross join data_source_dim ds
    where s.month_date is not null
      and s.location_fips_code is not null
)

select * from fact_data