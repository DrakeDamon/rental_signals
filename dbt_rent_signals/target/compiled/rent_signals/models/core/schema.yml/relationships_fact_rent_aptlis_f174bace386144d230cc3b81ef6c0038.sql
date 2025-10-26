
    
    

with child as (
    select location_key as from_field
    from RENTS.DBT_DEV_core.fact_rent_aptlist
    where location_key is not null
),

parent as (
    select location_key as to_field
    from RENTS.DBT_DEV_core.dim_location
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


