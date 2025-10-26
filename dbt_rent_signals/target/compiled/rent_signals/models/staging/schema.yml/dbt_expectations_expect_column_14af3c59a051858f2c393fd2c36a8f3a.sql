

with all_values as (

    select
        metro_size_category as value_field

    from RENTS.DBT_DEV_staging.stg_zori
    

),
set_values as (

    select
        cast('Top 10 Metros' as TEXT) as value_field
    union all
    select
        cast('Major Metros (11-50)' as TEXT) as value_field
    union all
    select
        cast('Large Metros (51-100)' as TEXT) as value_field
    union all
    select
        cast('Medium Metros (101-200)' as TEXT) as value_field
    union all
    select
        cast('Small Metros (200+)' as TEXT) as value_field
    
    
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

