{{
  config(
    materialized='table',
    description='Economic series dimension - simplified without SCD2'
  )
}}

select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['series_id']) }} as series_key,
    
    -- Business key
    series_id,
    series_business_key,
    
    -- Attributes
    series_label,
    category,
    seasonal_adjustment,
    frequency,
    source_name,
    source_system,
    
    -- Metadata
    reliability_score,
    update_frequency,
    collection_method,
    
    -- Simplified - no SCD2
    true as is_current,
    current_timestamp() as created_at,
    '{{ run_started_at }}' as dbt_run_id
    
from {{ ref('stg_fred') }}
-- Get distinct series (FRED data is already at series level)
qualify row_number() over (partition by series_id order by month_date desc) = 1

