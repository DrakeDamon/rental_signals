

with series_snapshot as (
    select * from RENTS.snapshots.snap_economic_series
),

dimension_table as (
    select
        -- Surrogate key
        md5(cast(coalesce(cast(series_business_key as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(dbt_valid_from as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as series_key,
        
        -- Business key
        series_id,
        series_business_key,
        
        -- Series attributes (can change over time)
        series_label,
        category,
        
        -- Derive subcategory from label
        case 
            when upper(series_label) like '%RENT%PRIMARY%' then 'Primary Residence Rent'
            when upper(series_label) like '%RENT%SHELTER%' then 'Shelter Rent'
            when upper(series_label) like '%MOTOR%FUEL%' then 'Motor Fuel'
            when upper(series_label) like '%APPAREL%' then 'Apparel'
            when upper(series_label) like '%MEDICAL%' then 'Medical Care'
            when upper(series_label) like '%TRANSPORTATION%' then 'Transportation'
            when upper(series_label) like '%RECREATION%' then 'Recreation'
            when upper(series_label) like '%EDUCATION%' then 'Education'
            when upper(series_label) like '%ALCOHOL%TOBACCO%' then 'Alcohol & Tobacco'
            else 'Other'
        end as subcategory,
        
        frequency,
        'Index' as units,  -- Most CPI series are index values
        seasonal_adjustment,
        '1982-84=100' as base_period,  -- Standard CPI base period
        
        -- Derive data start date from series ID patterns
        case
            when series_id like '%198%' then '1980-01-01'
            when series_id like '%199%' then '1990-01-01'
            when series_id like '%200%' then '2000-01-01'
            else '1980-01-01'  -- Conservative default
        end::date as data_start_date,
        
        series_label as description,
        
        -- SCD Type 2 fields
        dbt_valid_from as effective_date,
        dbt_valid_to as end_date,
        case when dbt_valid_to is null then true else false end as is_current,
        
        -- Source metadata
        source_name,
        source_system,
        update_frequency,
        collection_method,
        reliability_score,
        true as is_active,  -- FRED series are generally active
        
        -- Content hash for change detection
        series_content_hash,
        
        -- Metadata
        dbt_updated_at as updated_at,
        current_timestamp() as created_at,
        '2025-10-26 04:07:02.967691+00:00' as dbt_run_id
        
    from series_snapshot
)

select * from dimension_table