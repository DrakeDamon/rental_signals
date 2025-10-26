
    
    

select
    month_date as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_core.dim_time
where month_date is not null
group by month_date
having count(*) > 1


