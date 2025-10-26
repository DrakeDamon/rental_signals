






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and rent_value >= 0 and rent_value <= 15000
)
 as expression


    from RENTS.DBT_DEV_marts.mart_rent_trends
    

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







