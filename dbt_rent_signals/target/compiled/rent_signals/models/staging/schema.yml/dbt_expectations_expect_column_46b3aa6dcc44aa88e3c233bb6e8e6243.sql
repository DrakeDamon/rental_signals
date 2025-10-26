






    with grouped_expression as (
    select
        
        
    
  
( 1=1 and data_quality_score >= 1 and data_quality_score <= 10
)
 as expression


    from RENTS.DBT_DEV_staging.stg_zori
    

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







