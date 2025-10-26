



    with grouped_expression as (
    select
        
        
    
  
( 1=1 and count(*) >= 1000 and count(*) <= 1000000
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





