
    
    

select
    time_key as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_core.dim_time
where time_key is not null
group by time_key
having count(*) > 1


