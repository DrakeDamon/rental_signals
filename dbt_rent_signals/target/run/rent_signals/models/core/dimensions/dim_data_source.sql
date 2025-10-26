
  
    

create or replace transient table RENTS.DBT_DEV_core.dim_data_source
    
    
    
    as (

with source_systems as (
    select * from (
        values
            ('Zillow ZORI', 'Zillow', 'Rent Index', 'Monthly', 'Web Scraping', 9, 'Zillow Observed Rent Index for metro areas', 'https://www.zillow.com/research/', true),
            ('ApartmentList', 'ApartmentList', 'Rent Index', 'Monthly', 'Web Scraping', 8, 'Apartment List rent estimates by geography', 'https://www.apartmentlist.com/research/', true),
            ('FRED CPI', 'Federal Reserve', 'Economic Indicator', 'Monthly', 'API', 10, 'Consumer Price Index from Federal Reserve Economic Data', 'https://fred.stlouisfed.org/', true)
    ) as t(source_name, source_system, data_type, update_frequency, collection_method, reliability_score, description, website_url, is_active)
),

dimension_table as (
    select
        -- Surrogate key
        md5(cast(coalesce(cast(source_name as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as source_key,
        
        -- Source attributes
        source_name,
        source_system,
        data_type,
        update_frequency,
        collection_method,
        reliability_score,
        description,
        website_url,
        is_active,
        
        -- Additional metadata derived from source characteristics
        case 
            when collection_method = 'API' then 'High'
            when collection_method = 'Web Scraping' then 'Medium'
            else 'Low'
        end as data_freshness_expectation,
        
        case
            when reliability_score >= 9 then 'Excellent'
            when reliability_score >= 7 then 'Good'
            when reliability_score >= 5 then 'Fair'
            else 'Poor'
        end as reliability_category,
        
        case
            when update_frequency = 'Monthly' then 30
            when update_frequency = 'Weekly' then 7
            when update_frequency = 'Daily' then 1
            else 999
        end as expected_update_interval_days,
        
        -- Metadata
        current_timestamp() as created_at,
        current_timestamp() as updated_at,
        '2025-10-26 04:41:04.391014+00:00' as dbt_run_id
        
    from source_systems
)

select * from dimension_table
    )
;


  