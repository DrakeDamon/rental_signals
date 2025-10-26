{{
  config(
    materialized='table',
    description='Location dimension - simplified without SCD2 for initial deployment'
  )
}}

-- Combine location data from all sources
with all_locations as (
    -- ApartmentList locations
    select
        location_business_key,
        coalesce(location_fips_code, 'UNKNOWN') as location_fips_code,
        cast(regionid as varchar) as regionid,  -- Cast here to handle 'overall'
        location_name,
        location_type,
        state_name,
        county,
        metro,
        null as size_rank,
        population,
        'ApartmentList' as source_system
    from {{ ref('stg_aptlist') }}
    where location_business_key is not null
    
    union all
    
    -- Zillow ZORI locations  
    select
        location_business_key,
        null as location_fips_code,
        cast(regionid as varchar) as regionid,  -- Cast here too
        location_name,
        location_type,
        state_name,
        null as county,
        location_name as metro,
        size_rank,
        null as population,
        'Zillow ZORI' as source_system
    from {{ ref('stg_zori') }}
    where location_business_key is not null
),

-- Deduplicate and merge
merged_locations as (
    select distinct
        location_business_key,
        max(location_fips_code) as location_fips_code,
        max(regionid) as regionid,  -- Already cast in CTEs above
        max(location_name) as location_name,
        max(location_type) as location_type,
        max(state_name) as state_name,
        max(county) as county_name,
        max(metro) as metro_name,
        max(size_rank) as size_rank,
        max(population) as population,
        listagg(distinct source_system, ', ') within group (order by source_system) as source_systems
    from all_locations
    group by location_business_key
)

select
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['location_business_key']) }} as location_key,
    
    -- Business keys
    location_fips_code,
    regionid,
    location_business_key,
    
    -- Attributes
    location_name,
    location_type,
    state_name,
    county_name,
    metro_name,
    size_rank,
    population,
    
    -- Derived attributes
    case 
        when upper(state_name) like '%FLORIDA%' or upper(state_name) = 'FL' then 'FL'
        when upper(state_name) like '%CALIFORNIA%' or upper(state_name) = 'CA' then 'CA'
        when upper(state_name) like '%TEXAS%' or upper(state_name) = 'TX' then 'TX'
        when upper(state_name) like '%NEW YORK%' or upper(state_name) = 'NY' then 'NY'
        else left(upper(coalesce(state_name, 'UNKNOWN')), 2)
    end as state_code,
    
    case 
        when population >= 5000000 then 'Major Metro (5M+)'
        when population >= 1000000 then 'Large Metro (1M-5M)'
        when population >= 250000 then 'Medium Metro (250K-1M)'
        when population < 250000 then 'Small Metro (<250K)'
        else 'Unknown Size'
    end as market_size_category,
    
    case
        when size_rank <= 10 then 'Top 10 Markets'
        when size_rank <= 50 then 'Top 50 Markets'
        when size_rank <= 100 then 'Top 100 Markets'
        when size_rank <= 200 then 'Large Markets'
        else 'Small Markets'
    end as size_rank_category,
    
    -- Source tracking
    source_systems,
    
    -- Metadata (simplified - no SCD2)
    true as is_current,
    current_timestamp() as created_at,
    '{{ run_started_at }}' as dbt_run_id
    
from merged_locations

