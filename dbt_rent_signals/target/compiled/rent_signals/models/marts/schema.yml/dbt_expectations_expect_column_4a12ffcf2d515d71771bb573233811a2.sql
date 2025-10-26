

with all_values as (

    select
        affordability_category as value_field

    from RENTS.DBT_DEV_marts.mart_rent_trends
    

),
set_values as (

    select
        cast('Very Expensive' as TEXT) as value_field
    union all
    select
        cast('Expensive' as TEXT) as value_field
    union all
    select
        cast('Moderate' as TEXT) as value_field
    union all
    select
        cast('Affordable' as TEXT) as value_field
    union all
    select
        cast('Very Affordable' as TEXT) as value_field
    
    
),
validation_errors as (
    -- values from the model that are not in the set
    select
        v.value_field
    from
        all_values v
        left join
        set_values s on v.value_field = s.value_field
    where
        s.value_field is null

)

select *
from validation_errors

