
    
    

with child as (
    select series_key as from_field
    from RENTS.DBT_DEV_core.fact_economic_indicator
    where series_key is not null
),

parent as (
    select series_key as to_field
    from RENTS.DBT_DEV_core.dim_economic_series
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


