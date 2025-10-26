
  
    

create or replace transient table RENTS.DBT_DEV_core.dim_economic_series
    
    
    
    as (

select
    -- Surrogate key
    md5(cast(coalesce(cast(series_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as series_key,
    
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
    '2025-10-26 04:41:04.391014+00:00' as dbt_run_id
    
from RENTS.DBT_DEV_staging.stg_fred
-- Get distinct series (FRED data is already at series level)
qualify row_number() over (partition by series_id order by month_date desc) = 1
    )
;


  