

with all_values as (

    select
        economic_regime as value_field

    from RENTS.DBT_DEV_marts.mart_economic_correlation
    

),
set_values as (

    select
        cast('High Inflation + Hot Rent Market' as TEXT) as value_field
    union all
    select
        cast('Moderate Inflation + Growing Rents' as TEXT) as value_field
    union all
    select
        cast('Low Inflation + Stable Rents' as TEXT) as value_field
    union all
    select
        cast('Stagflation Risk' as TEXT) as value_field
    union all
    select
        cast('Deflationary Pressure' as TEXT) as value_field
    union all
    select
        cast('Transitional Period' as TEXT) as value_field
    
    
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

