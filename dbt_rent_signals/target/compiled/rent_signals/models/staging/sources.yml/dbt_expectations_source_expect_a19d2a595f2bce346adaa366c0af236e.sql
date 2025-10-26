






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and rent_index >= 0 and rent_index <= 2000
)
 as expression


    from RENTS.RAW.aptlist_long
    

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







