
    
    

select
    location_business_key as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_staging.stg_zori
where location_business_key is not null
group by location_business_key
having count(*) > 1


