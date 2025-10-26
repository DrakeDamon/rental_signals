

with all_values as (

    select
        market_temperature as value_field

    from RENTS.DBT_DEV_marts.mart_regional_summary
    

),
set_values as (

    select
        cast('Overheating' as TEXT) as value_field
    union all
    select
        cast('Very Hot' as TEXT) as value_field
    union all
    select
        cast('Hot' as TEXT) as value_field
    union all
    select
        cast('Warm' as TEXT) as value_field
    union all
    select
        cast('Cool' as TEXT) as value_field
    union all
    select
        cast('Cold' as TEXT) as value_field
    union all
    select
        cast('Frozen' as TEXT) as value_field
    
    
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

