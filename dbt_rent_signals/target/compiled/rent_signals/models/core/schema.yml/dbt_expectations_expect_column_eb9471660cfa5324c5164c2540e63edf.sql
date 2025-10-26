

with all_values as (

    select
        inflation_category as value_field

    from RENTS.DBT_DEV_core.fact_economic_indicator
    

),
set_values as (

    select
        cast('High Inflation' as TEXT) as value_field
    union all
    select
        cast('Moderate Inflation' as TEXT) as value_field
    union all
    select
        cast('Low Inflation' as TEXT) as value_field
    union all
    select
        cast('Stable Prices' as TEXT) as value_field
    union all
    select
        cast('Deflation' as TEXT) as value_field
    union all
    select
        cast('Insufficient History' as TEXT) as value_field
    union all
    select
        cast('Not Applicable' as TEXT) as value_field
    
    
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

