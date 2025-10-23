{{
  config(
    materialized='view',
    description='Cleaned and standardized FRED economic indicator data from raw CSV imports'
  )
}}

with source_data as (
    select * from {{ source('raw', 'fred_cpi_long') }}
),

cleaned as (
    select
        -- Business keys and identifiers
        series_id,
        label as series_label,
        
        -- Temporal dimension
        month as month_date,
        
        -- Metrics
        value as indicator_value,
        
        -- Parse and categorize economic series
        case 
            when upper(label) like '%HOUSING%' or upper(label) like '%SHELTER%' then 'Housing CPI'
            when upper(label) like '%CORE%' then 'Core CPI'
            when upper(label) like '%ALL ITEMS%' then 'All Items CPI'
            when upper(label) like '%ENERGY%' then 'Energy CPI'
            when upper(label) like '%FOOD%' then 'Food CPI'
            else 'Other CPI'
        end as category,
        
        case 
            when upper(label) like '%SEASONA%ADJ%' or upper(label) like '%SA%' then 'SA'
            when upper(label) like '%NOT%SEASONA%' or upper(label) like '%NSA%' then 'NSA'
            else 'Unknown'
        end as seasonal_adjustment,
        
        case
            when upper(label) like '%ANNUAL%' or upper(label) like '%YEAR%' then 'Annual'
            when upper(label) like '%MONTH%' then 'Monthly'
            when upper(label) like '%QUARTER%' then 'Quarterly'
            else 'Monthly'  -- Default assumption
        end as frequency,
        
        -- Data quality and lineage
        current_timestamp() as processed_at,
        '{{ run_started_at }}' as dbt_run_id,
        
        -- Create business key for series
        {{ dbt_utils.generate_surrogate_key([
            'series_id'
        ]) }} as series_business_key,
        
        -- Create content hash for SCD2 change detection
        {{ dbt_utils.generate_surrogate_key([
            'label',
            'category',
            'seasonal_adjustment',
            'frequency'
        ]) }} as series_content_hash,
        
        -- Row-level data quality scoring
        case
            when value is null then 1
            when value < 0 and series_id not like '%CHG%' then 3  -- Negative values might be valid for change series
            when series_id is null then 2
            when label is null then 4
            else 10
        end as data_quality_score,
        
        -- Outlier detection for CPI values
        case
            when series_id like '%CPI%' and value > 1000 then true  -- CPI values rarely exceed 1000
            when series_id like '%CPI%' and value < 0 then true     -- CPI shouldn't be negative
            when abs(value) > (
                select avg(abs(value)) + 4 * stddev(abs(value)) 
                from {{ source('raw', 'fred_cpi_long') }}
                where value is not null and series_id = source_data.series_id
            ) then true
            else false
        end as has_anomaly,
        
        -- Additional metadata
        'Federal Reserve Economic Data' as source_name,
        'FRED' as source_system,
        'Monthly' as update_frequency,
        'API' as collection_method,
        10 as reliability_score  -- FRED is highly reliable
        
    from source_data
    where 
        -- Data quality filters
        month is not null
        and series_id is not null
        and label is not null
        and value is not null
        -- Date boundary filters
        and month >= '{{ var("start_date") }}'
        and month <= '{{ var("end_date") }}'
)

select * from cleaned