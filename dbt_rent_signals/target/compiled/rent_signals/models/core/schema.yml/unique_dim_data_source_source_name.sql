
    
    

select
    source_name as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_core.dim_data_source
where source_name is not null
group by source_name
having count(*) > 1


