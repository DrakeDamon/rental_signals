

with source_data as (
    select * from RENTS.RAW.zori_metro_long
),

cleaned as (
    select
        -- Business keys and identifiers
        regionid,
        sizerank as size_rank,
        metro as location_name,
        region_type as location_type,
        state_name,
        
        -- Temporal dimension
        month as month_date,
        
        -- Metrics
        zori as zori_value,
        
        -- Data quality and lineage
        current_timestamp() as processed_at,
        '2025-10-26 04:41:04.391014+00:00' as dbt_run_id,
        
        -- Create business key for location matching
        md5(cast(coalesce(cast(regionid as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as location_business_key,
        
        -- Create content hash for SCD2 change detection
        md5(cast(coalesce(cast(metro as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(region_type as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(state_name as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(sizerank as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as location_content_hash,
        
        -- Row-level data quality scoring
        case
            when zori is null then 1
            when zori <= 0 then 2
            when zori > 10000 then 5  -- Flag unreasonably high rent values
            when regionid is null then 3
            when metro is null then 4
            else 10
        end as data_quality_score,
        
        -- Statistical anomaly detection
        case
            when zori > (
                select percentile_cont(0.99) within group (order by zori)
                from RENTS.RAW.zori_metro_long
                where zori is not null and zori > 0
            ) then true
            when zori < (
                select percentile_cont(0.01) within group (order by zori)
                from RENTS.RAW.zori_metro_long
                where zori is not null and zori > 0
            ) then true
            else false
        end as has_anomaly,
        
        -- Metro size categorization for analysis
        case
            when sizerank <= 10 then 'Top 10 Metros'
            when sizerank <= 50 then 'Major Metros (11-50)'
            when sizerank <= 100 then 'Large Metros (51-100)'
            when sizerank <= 200 then 'Medium Metros (101-200)'
            else 'Small Metros (200+)'
        end as metro_size_category
        
    from source_data
    where 
        -- Data quality filters
        month is not null
        and regionid is not null
        and metro is not null
        and zori is not null
        and zori > 0
        -- Date boundary filters
        and month >= '2015-01-01'
        and month <= '2030-12-31'
)

select * from cleaned