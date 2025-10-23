{{
  config(
    materialized='table',
    description='Economic indicator facts with calculated measures and revision tracking'
  )
}}

with staging_data as (
    select * from {{ ref('stg_fred') }}
),

time_dim as (
    select * from {{ ref('dim_time') }}
),

series_dim as (
    select * from {{ ref('dim_economic_series') }}
    where is_current = true
),

data_source_dim as (
    select * from {{ ref('dim_data_source') }}
    where source_name = 'FRED CPI'
),

fact_data as (
    select
        -- Dimension foreign keys
        t.time_key,
        es.series_key,
        ds.source_key,
        
        -- Business keys for debugging
        s.series_id,
        s.month_date,
        
        -- Measures
        s.indicator_value,
        
        -- Calculate year-over-year and month-over-month changes
        {{ calculate_changes('s.indicator_value', 's.series_id') }},
        
        -- Record count (always 1 for grain validation)
        1 as record_count,
        
        -- Enhanced data quality scoring for economic indicators
        case
            when s.indicator_value is null then 1
            when s.series_id is null then 2
            when s.series_label is null then 3
            when s.series_id like '%CPI%' and s.indicator_value < 0 then 4  -- CPI shouldn't be negative
            when s.series_id like '%CPI%' and s.indicator_value > 1000 then 5  -- CPI rarely exceeds 1000
            when abs(s.indicator_value) > (
                select avg(abs(indicator_value)) + 3 * stddev(abs(indicator_value)) 
                from {{ ref('stg_fred') }} stg_inner
                where stg_inner.series_id = s.series_id
                and stg_inner.indicator_value is not null
            ) then 6  -- Statistical outlier
            else 10
        end as data_quality_score,
        
        -- Basic revision tracking (would need historical data to fully implement)
        false as is_revised,
        0 as revision_count,
        
        -- Enhanced measures for economic analysis
        -- Trend classification for CPI data
        case 
            when s.series_id like '%CPI%' and lag(s.indicator_value, 12) over (
                partition by s.series_id 
                order by s.month_date
            ) is null then 'Insufficient History'
            when s.series_id like '%CPI%' and (
                (s.indicator_value - lag(s.indicator_value, 12) over (
                    partition by s.series_id 
                    order by s.month_date
                )) / nullif(lag(s.indicator_value, 12) over (
                    partition by s.series_id 
                    order by s.month_date
                ), 0) * 100
            ) > 5 then 'High Inflation'
            when s.series_id like '%CPI%' and (
                (s.indicator_value - lag(s.indicator_value, 12) over (
                    partition by s.series_id 
                    order by s.month_date
                )) / nullif(lag(s.indicator_value, 12) over (
                    partition by s.series_id 
                    order by s.month_date
                ), 0) * 100
            ) > 2 then 'Moderate Inflation'
            when s.series_id like '%CPI%' and (
                (s.indicator_value - lag(s.indicator_value, 12) over (
                    partition by s.series_id 
                    order by s.month_date
                )) / nullif(lag(s.indicator_value, 12) over (
                    partition by s.series_id 
                    order by s.month_date
                ), 0) * 100
            ) > 0 then 'Low Inflation'
            when s.series_id like '%CPI%' and (
                (s.indicator_value - lag(s.indicator_value, 12) over (
                    partition by s.series_id 
                    order by s.month_date
                )) / nullif(lag(s.indicator_value, 12) over (
                    partition by s.series_id 
                    order by s.month_date
                ), 0) * 100
            ) >= 0 then 'Stable Prices'
            when s.series_id like '%CPI%' then 'Deflation'
            else 'Not Applicable'
        end as inflation_category,
        
        -- Rolling averages for smoothing
        avg(s.indicator_value) over (
            partition by s.series_id 
            order by s.month_date 
            rows between 2 preceding and current row
        ) as three_month_avg,
        
        avg(s.indicator_value) over (
            partition by s.series_id 
            order by s.month_date 
            rows between 5 preceding and current row
        ) as six_month_avg,
        
        avg(s.indicator_value) over (
            partition by s.series_id 
            order by s.month_date 
            rows between 11 preceding and current row
        ) as twelve_month_avg,
        
        -- Volatility measures
        stddev(s.indicator_value) over (
            partition by s.series_id 
            order by s.month_date 
            rows between 11 preceding and current row
        ) as twelve_month_volatility,
        
        -- Data lineage
        current_timestamp() as load_date,
        'fred_cpi_long.csv' as source_file_name,
        s.processed_at,
        s.dbt_run_id
        
    from staging_data s
    inner join time_dim t on 
        year(s.month_date) * 100 + month(s.month_date) = t.time_key
    inner join series_dim es on 
        s.series_id = es.series_id
    cross join data_source_dim ds
)

select * from fact_data