






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and record_count >= 0 and record_count <= 10000000
)
 as expression


    from RENTS.DBT_DEV_marts.mart_data_lineage
    

),
validation_errors as (

    select
        *
    from
        grouped_expression
    where
        not(expression = true)

)

select *
from validation_errors







