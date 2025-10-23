{{
  config(
    materialized='view',
    description='Cleaned and standardized ApartmentList rent data from raw CSV imports'
  )
}}

with source_data as (
    select * from {{ source('raw', 'aptlist_long') }}
),

cleaned as (
    select
        -- Business keys and identifiers
        location_fips_code,
        regionid,
        location_name,
        location_type,
        state as state_name,
        county,
        metro,
        
        -- Temporal dimension
        month as month_date,
        
        -- Metrics
        rent_index,
        population,
        
        -- Data quality and lineage
        current_timestamp() as processed_at,
        '{{ run_started_at }}' as dbt_run_id,
        
        -- Create row hash for change detection
        {{ dbt_utils.generate_surrogate_key([
            'location_fips_code', 
            'regionid',
            'location_name',
            'location_type',
            'state',
            'county', 
            'metro'
        ]) }} as location_business_key,
        
        -- Create content hash for SCD2 change detection
        {{ dbt_utils.generate_surrogate_key([
            'location_name',
            'location_type', 
            'state',
            'county',
            'metro',
            'population'
        ]) }} as location_content_hash,
        
        -- Row-level data quality scoring
        case
            when rent_index is null then 1
            when rent_index <= 0 then 2
            when rent_index > 1000 then 5  -- Flag very high index values
            when population is null then 6
            when population <= 0 then 7
            else 10
        end as data_quality_score,
        
        -- Basic anomaly detection flag
        case
            when rent_index > (
                select avg(rent_index) + 3 * stddev(rent_index) 
                from {{ source('raw', 'aptlist_long') }}
                where rent_index is not null
            ) then true
            when rent_index < (
                select avg(rent_index) - 3 * stddev(rent_index) 
                from {{ source('raw', 'aptlist_long') }}
                where rent_index is not null and rent_index > 0
            ) then true
            else false
        end as has_anomaly
        
    from source_data
    where 
        -- Data quality filters
        month is not null
        and location_name is not null
        and rent_index is not null
        and rent_index > 0
        -- Date boundary filters
        and month >= '{{ var("start_date") }}'
        and month <= '{{ var("end_date") }}'
)

select * from cleaned