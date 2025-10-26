

with all_values as (

    select
        temporal_coverage as value_field

    from RENTS.DBT_DEV_marts.mart_data_lineage
    

),
set_values as (

    select
        cast('Excellent Coverage (5+ years)' as TEXT) as value_field
    union all
    select
        cast('Good Coverage (3-5 years)' as TEXT) as value_field
    union all
    select
        cast('Fair Coverage (1-3 years)' as TEXT) as value_field
    union all
    select
        cast('Limited Coverage (<1 year)' as TEXT) as value_field
    
    
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

