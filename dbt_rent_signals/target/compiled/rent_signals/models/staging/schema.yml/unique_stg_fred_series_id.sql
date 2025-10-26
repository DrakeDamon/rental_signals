
    
    

select
    series_id as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_staging.stg_fred
where series_id is not null
group by series_id
having count(*) > 1


