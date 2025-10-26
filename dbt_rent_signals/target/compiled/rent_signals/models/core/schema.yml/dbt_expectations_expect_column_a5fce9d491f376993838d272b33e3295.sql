

with all_values as (

    select
        growth_category as value_field

    from RENTS.DBT_DEV_core.fact_rent_aptlist
    

),
set_values as (

    select
        cast('Very High Growth' as TEXT) as value_field
    union all
    select
        cast('High Growth' as TEXT) as value_field
    union all
    select
        cast('Moderate Growth' as TEXT) as value_field
    union all
    select
        cast('Low Growth' as TEXT) as value_field
    union all
    select
        cast('Slight Decline' as TEXT) as value_field
    union all
    select
        cast('Significant Decline' as TEXT) as value_field
    union all
    select
        cast('Insufficient History' as TEXT) as value_field
    
    
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

