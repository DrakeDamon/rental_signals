






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and market_heat_score >= 0 and market_heat_score <= 100
)
 as expression


    from RENTS.DBT_DEV_marts.mart_market_rankings
    

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







