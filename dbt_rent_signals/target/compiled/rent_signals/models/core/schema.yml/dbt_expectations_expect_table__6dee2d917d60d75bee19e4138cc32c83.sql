



    with grouped_expression as (
    select
        
        
    
  
( 1=1 and count(*) >= 100 and count(*) <= 500
)
 as expression


    from RENTS.DBT_DEV_core.dim_time
    

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





