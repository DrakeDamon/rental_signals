

with all_values as (

    select
        category as value_field

    from RENTS.DBT_DEV_core.dim_economic_series
    

),
set_values as (

    select
        cast('Housing CPI' as TEXT) as value_field
    union all
    select
        cast('Core CPI' as TEXT) as value_field
    union all
    select
        cast('All Items CPI' as TEXT) as value_field
    union all
    select
        cast('Energy CPI' as TEXT) as value_field
    union all
    select
        cast('Food CPI' as TEXT) as value_field
    union all
    select
        cast('Other CPI' as TEXT) as value_field
    
    
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

