

with all_values as (

    select
        market_size_category as value_field

    from RENTS.DBT_DEV_core.dim_location
    

),
set_values as (

    select
        cast('Major Metro (5M+)' as TEXT) as value_field
    union all
    select
        cast('Large Metro (1M-5M)' as TEXT) as value_field
    union all
    select
        cast('Medium Metro (250K-1M)' as TEXT) as value_field
    union all
    select
        cast('Small Metro (<250K)' as TEXT) as value_field
    union all
    select
        cast('Unknown Size' as TEXT) as value_field
    
    
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

