{% snapshot snap_economic_series %}

{{
    config(
      target_schema='snapshots',
      unique_key='series_business_key',
      strategy='check',
      check_cols=['series_content_hash'],
      invalidate_hard_deletes=True
    )
}}

-- Economic series metadata from FRED with change tracking
select
    series_business_key,
    series_content_hash,
    series_id,
    series_label,
    category,
    seasonal_adjustment,
    frequency,
    source_name,
    source_system,
    update_frequency,
    collection_method,
    reliability_score
from {{ ref('stg_fred') }}
where series_business_key is not null
qualify row_number() over (
    partition by series_business_key, series_content_hash 
    order by month_date desc
) = 1

{% endsnapshot %}