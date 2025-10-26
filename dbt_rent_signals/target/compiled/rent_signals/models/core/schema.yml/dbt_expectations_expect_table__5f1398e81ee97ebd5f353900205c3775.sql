



    with grouped_expression as (
    select
        
        
    
  
( 1=1 and count(*) >= 50 and count(*) <= 2000
)
 as expression


    from RENTS.DBT_DEV_core.dim_location
    

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





