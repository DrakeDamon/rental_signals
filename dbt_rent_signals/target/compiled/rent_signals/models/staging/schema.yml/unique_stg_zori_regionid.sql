
    
    

select
    regionid as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_staging.stg_zori
where regionid is not null
group by regionid
having count(*) > 1


