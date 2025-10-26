






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and zori >= 0 and zori <= 15000
)
 as expression


    from RENTS.RAW.zori_metro_long
    

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







