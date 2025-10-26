






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and zori_value >= 0 and zori_value <= 15000
)
 as expression


    from RENTS.DBT_DEV_core.fact_rent_zori
    

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







