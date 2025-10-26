
    
    

select
    location_name as unique_field,
    count(*) as n_records

from RENTS.DBT_DEV_marts.mart_market_rankings
where location_name is not null
group by location_name
having count(*) > 1


