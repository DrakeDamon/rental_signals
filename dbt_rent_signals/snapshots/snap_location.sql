{% snapshot snap_location %}

{{
    config(
      target_schema='snapshots',
      unique_key='location_business_key',
      strategy='check',
      check_cols=['location_content_hash'],
      invalidate_hard_deletes=True
    )
}}

-- Combine location data from all sources for comprehensive SCD2 tracking
with all_locations as (
    -- ApartmentList locations
    select
        location_business_key,
        location_content_hash,
        coalesce(location_fips_code, 'UNKNOWN') as location_fips_code,
        regionid,
        location_name,
        location_type,
        state_name,
        county,
        metro,
        null as size_rank,  -- Not available in ApartmentList
        population,
        'ApartmentList' as source_system
    from {{ ref('stg_aptlist') }}
    where location_business_key is not null
    
    union all
    
    -- Zillow ZORI locations  
    select
        location_business_key,
        location_content_hash,
        null as location_fips_code,  -- Not available in ZORI
        regionid,
        location_name,
        location_type,
        state_name,
        null as county,  -- Not available in ZORI
        location_name as metro,  -- ZORI location_name is metro
        size_rank,
        null as population,  -- Not available in ZORI
        'Zillow ZORI' as source_system
    from {{ ref('stg_zori') }}
    where location_business_key is not null
),

-- Deduplicate and merge location attributes
merged_locations as (
    select
        location_business_key,
        location_content_hash,
        
        -- Use first non-null value for each attribute
        first_value(location_fips_code ignore nulls) over (
            partition by location_business_key 
            order by case when location_fips_code is not null then 1 else 2 end
        ) as location_fips_code,
        
        first_value(regionid ignore nulls) over (
            partition by location_business_key 
            order by case when regionid is not null then 1 else 2 end
        ) as regionid,
        
        first_value(location_name ignore nulls) over (
            partition by location_business_key 
            order by case when location_name is not null then 1 else 2 end
        ) as location_name,
        
        first_value(location_type ignore nulls) over (
            partition by location_business_key 
            order by case when location_type is not null then 1 else 2 end
        ) as location_type,
        
        first_value(state_name ignore nulls) over (
            partition by location_business_key 
            order by case when state_name is not null then 1 else 2 end
        ) as state_name,
        
        first_value(county ignore nulls) over (
            partition by location_business_key 
            order by case when county is not null then 1 else 2 end
        ) as county_name,
        
        first_value(metro ignore nulls) over (
            partition by location_business_key 
            order by case when metro is not null then 1 else 2 end
        ) as metro_name,
        
        first_value(size_rank ignore nulls) over (
            partition by location_business_key 
            order by case when size_rank is not null then 1 else 2 end
        ) as size_rank,
        
        first_value(population ignore nulls) over (
            partition by location_business_key 
            order by case when population is not null then 1 else 2 end
        ) as population,
        
        -- Combine source systems
        listagg(distinct source_system, ', ') over (
            partition by location_business_key
        ) as source_systems
        
    from all_locations
    qualify row_number() over (
        partition by location_business_key, location_content_hash 
        order by source_system
    ) = 1
)

select * from merged_locations

{% endsnapshot %}