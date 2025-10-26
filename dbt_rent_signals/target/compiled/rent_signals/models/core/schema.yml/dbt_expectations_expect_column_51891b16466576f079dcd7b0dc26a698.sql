

with all_values as (

    select
        rental_season as value_field

    from RENTS.DBT_DEV_core.dim_time
    

),
set_values as (

    select
        cast('Peak Moving Season' as TEXT) as value_field
    union all
    select
        cast('Low Moving Season' as TEXT) as value_field
    union all
    select
        cast('Normal Season' as TEXT) as value_field
    
    
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

