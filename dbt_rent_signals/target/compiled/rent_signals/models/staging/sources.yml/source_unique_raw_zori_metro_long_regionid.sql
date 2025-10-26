
    
    

select
    regionid as unique_field,
    count(*) as n_records

from RENTS.RAW.zori_metro_long
where regionid is not null
group by regionid
having count(*) > 1


