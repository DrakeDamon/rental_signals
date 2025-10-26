






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and overall_reliability_score >= 0 and overall_reliability_score <= 100
)
 as expression


    from RENTS.DBT_DEV_marts.mart_data_lineage
    

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







