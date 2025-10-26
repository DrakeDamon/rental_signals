

with all_values as (

    select
        investment_recommendation as value_field

    from RENTS.DBT_DEV_marts.mart_market_rankings
    

),
set_values as (

    select
        cast('Strong Buy' as TEXT) as value_field
    union all
    select
        cast('Buy' as TEXT) as value_field
    union all
    select
        cast('Hold' as TEXT) as value_field
    union all
    select
        cast('Caution' as TEXT) as value_field
    union all
    select
        cast('Avoid' as TEXT) as value_field
    
    
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

