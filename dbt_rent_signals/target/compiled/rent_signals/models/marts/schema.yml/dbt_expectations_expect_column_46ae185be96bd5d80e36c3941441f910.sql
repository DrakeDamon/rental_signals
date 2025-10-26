

with all_values as (

    select
        policy_implications as value_field

    from RENTS.DBT_DEV_marts.mart_economic_correlation
    

),
set_values as (

    select
        cast('Consider Rent Controls' as TEXT) as value_field
    union all
    select
        cast('Housing Supply Crisis' as TEXT) as value_field
    union all
    select
        cast('Economic Divergence' as TEXT) as value_field
    union all
    select
        cast('Market Equilibrium' as TEXT) as value_field
    union all
    select
        cast('Monitor Trends' as TEXT) as value_field
    
    
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

