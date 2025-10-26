
    
    

select
    series_business_key as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_staging.stg_fred
where series_business_key is not null
group by series_business_key
having count(*) > 1


