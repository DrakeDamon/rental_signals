
    
    

select
    source_key as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_core.dim_data_source
where source_key is not null
group by source_key
having count(*) > 1


