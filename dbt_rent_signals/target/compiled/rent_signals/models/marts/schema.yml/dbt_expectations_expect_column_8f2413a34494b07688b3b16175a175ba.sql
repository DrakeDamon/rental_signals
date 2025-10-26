






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and location_count >= 1 and location_count <= 1000
)
 as expression


    from RENTS.DBT_DEV_marts.mart_regional_summary
    

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







