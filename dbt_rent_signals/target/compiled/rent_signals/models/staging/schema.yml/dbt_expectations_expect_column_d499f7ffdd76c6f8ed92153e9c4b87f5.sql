






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and month_date >= '2015-01-01' and month_date <= '2030-12-31'
)
 as expression


    from RENTS.DBT_DEV_staging.stg_fred
    

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







