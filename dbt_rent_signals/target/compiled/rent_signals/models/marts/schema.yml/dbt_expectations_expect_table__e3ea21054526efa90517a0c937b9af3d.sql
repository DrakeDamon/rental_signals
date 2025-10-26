



    with grouped_expression as (
    select
        
        
    
  
( 1=1 and count(*) >= 10 and count(*) <= 100
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





