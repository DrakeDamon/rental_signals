

with all_values as (

    select
        table_name as value_field

    from RENTS.DBT_DEV_marts.mart_data_lineage
    

),
set_values as (

    select
        cast('FACT_RENT_ZORI' as TEXT) as value_field
    union all
    select
        cast('FACT_RENT_APTLIST' as TEXT) as value_field
    union all
    select
        cast('FACT_ECONOMIC_INDICATOR' as TEXT) as value_field
    
    
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

