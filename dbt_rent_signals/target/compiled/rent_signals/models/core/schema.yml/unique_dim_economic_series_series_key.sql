
    
    

select
    series_key as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_core.dim_economic_series
where series_key is not null
group by series_key
having count(*) > 1


