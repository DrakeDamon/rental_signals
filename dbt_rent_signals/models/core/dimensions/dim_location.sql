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
    
    -- Geographic coordinates for map visualization
    case 
        when location_name ilike '%Tampa%St%Petersburg%' then 27.9506
        when location_name ilike '%Miami%' then 25.7617
        when location_name ilike '%Orlando%' then 28.5383
        when location_name ilike '%Jacksonville%' then 30.3322
        when location_name ilike '%New York%' then 40.7128
        when location_name ilike '%Los Angeles%' then 34.0522
        when location_name ilike '%Chicago%' then 41.8781
        when location_name ilike '%Houston%' then 29.7604
        when location_name ilike '%Phoenix%' then 33.4484
        when location_name ilike '%Philadelphia%' then 39.9526
        when location_name ilike '%San Antonio%' then 29.4241
        when location_name ilike '%San Diego%' then 32.7157
        when location_name ilike '%Dallas%' then 32.7767
        when location_name ilike '%San Jose%' then 37.3382
        when location_name ilike '%Austin%' then 30.2672
        when location_name ilike '%Fort Worth%' then 32.7555
        when location_name ilike '%Columbus%' then 39.9612
        when location_name ilike '%Charlotte%' then 35.2271
        when location_name ilike '%San Francisco%' then 37.7749
        when location_name ilike '%Indianapolis%' then 39.7684
        when location_name ilike '%Seattle%' then 47.6062
        when location_name ilike '%Denver%' then 39.7392
        when location_name ilike '%Boston%' then 42.3601
        when location_name ilike '%Nashville%' then 36.1627
        when location_name ilike '%Detroit%' then 42.3314
        when location_name ilike '%Portland%' then 45.5152
        when location_name ilike '%Las Vegas%' then 36.1699
        when location_name ilike '%Atlanta%' then 33.7490
        when location_name ilike '%Raleigh%' then 35.7796
        when location_name ilike '%Minneapolis%' then 44.9778
        else null
    end as latitude,
    
    case 
        when location_name ilike '%Tampa%St%Petersburg%' then -82.4572
        when location_name ilike '%Miami%' then -80.1918
        when location_name ilike '%Orlando%' then -81.3792
        when location_name ilike '%Jacksonville%' then -81.6557
        when location_name ilike '%New York%' then -74.0060
        when location_name ilike '%Los Angeles%' then -118.2437
        when location_name ilike '%Chicago%' then -87.6298
        when location_name ilike '%Houston%' then -95.3698
        when location_name ilike '%Phoenix%' then -112.0740
        when location_name ilike '%Philadelphia%' then -75.1652
        when location_name ilike '%San Antonio%' then -98.4936
        when location_name ilike '%San Diego%' then -117.1611
        when location_name ilike '%Dallas%' then -96.7970
        when location_name ilike '%San Jose%' then -121.8863
        when location_name ilike '%Austin%' then -97.7431
        when location_name ilike '%Fort Worth%' then -97.3308
        when location_name ilike '%Columbus%' then -82.9988
        when location_name ilike '%Charlotte%' then -80.8431
        when location_name ilike '%San Francisco%' then -122.4194
        when location_name ilike '%Indianapolis%' then -86.1581
        when location_name ilike '%Seattle%' then -122.3321
        when location_name ilike '%Denver%' then -104.9903
        when location_name ilike '%Boston%' then -71.0589
        when location_name ilike '%Nashville%' then -86.7816
        when location_name ilike '%Detroit%' then -83.0458
        when location_name ilike '%Portland%' then -122.6784
        when location_name ilike '%Las Vegas%' then -115.1398
        when location_name ilike '%Atlanta%' then -84.3880
        when location_name ilike '%Raleigh%' then -78.6382
        when location_name ilike '%Minneapolis%' then -93.2650
        else null
    end as longitude,
    
    -- URL-friendly metro slug for routing
    lower(
        replace(
            replace(
                replace(
                    replace(location_name, ', ', '-'),
                    ' ', '-'
                ),
                ',', ''
            ),
            '--', '-'
        )
    ) as metro_slug,
    
    -- Source tracking
    source_systems,
    
    -- Metadata (simplified - no SCD2)
    true as is_current,
    current_timestamp() as created_at,
    '{{ run_started_at }}' as dbt_run_id
    
from merged_locations

