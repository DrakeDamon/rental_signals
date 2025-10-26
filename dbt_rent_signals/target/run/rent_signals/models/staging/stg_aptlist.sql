
  create or replace   view RENTS.DBT_DEV_staging.stg_aptlist
  
  
  
  
  as (
    

with source_data as (
    select * from RENTS.RAW.aptlist_long
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
        '2025-10-26 04:41:04.391014+00:00' as dbt_run_id,
        
        -- Create row hash for change detection
        md5(cast(coalesce(cast(location_fips_code as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(regionid as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(location_name as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(location_type as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(state as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(county as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(metro as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as location_business_key,
        
        -- Create content hash for SCD2 change detection
        md5(cast(coalesce(cast(location_name as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(location_type as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(state as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(county as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(metro as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(population as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as location_content_hash,
        
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
                from RENTS.RAW.aptlist_long
                where rent_index is not null
            ) then true
            when rent_index < (
                select avg(rent_index) - 3 * stddev(rent_index) 
                from RENTS.RAW.aptlist_long
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
        and month >= '2015-01-01'
        and month <= '2030-12-31'
)

select * from cleaned
  );

