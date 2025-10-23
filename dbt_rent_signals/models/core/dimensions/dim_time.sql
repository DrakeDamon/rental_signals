{{
  config(
    materialized='table',
    description='Calendar dimension table with monthly grain for rent data analysis'
  )
}}

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="month",
        start_date="to_date('" ~ var('start_date') ~ "', 'yyyy-mm-dd')",
        end_date="to_date('" ~ var('end_date') ~ "', 'yyyy-mm-dd')"
    ) }}
),

calendar_attributes as (
    select
        -- Primary key - YYYYMM format for easy joins
        year(date_month) * 100 + month(date_month) as time_key,
        
        -- Date attributes
        date_month as month_date,
        year(date_month) as year,
        quarter(date_month) as quarter,
        month(date_month) as month_number,
        monthname(date_month) as month_name,
        dayname(date_month) as day_name,
        
        -- Formatted date strings
        'Q' || quarter(date_month) || ' ' || year(date_month) as quarter_name,
        to_char(date_month, 'YYYY-MM') as year_month,
        to_char(date_month, 'MON YYYY') as month_year_name,
        
        -- Fiscal year (October start)
        case 
            when month(date_month) >= 10 then year(date_month) + 1
            else year(date_month)
        end as fiscal_year,
        
        case 
            when month(date_month) >= 10 then quarter(date_month) - 2
            when month(date_month) >= 7 then quarter(date_month) + 2
            when month(date_month) >= 4 then quarter(date_month) + 1
            else quarter(date_month)
        end as fiscal_quarter,
        
        -- Relative date flags and calculations
        date_month = date_trunc('month', current_date()) as is_current_month,
        date_month = dateadd('month', -1, date_trunc('month', current_date())) as is_previous_month,
        date_month >= date_trunc('year', current_date()) as is_current_year,
        date_month >= date_trunc('quarter', current_date()) as is_current_quarter,
        
        -- Months ago calculation (0 = current month, 1 = last month, etc.)
        datediff('month', date_month, date_trunc('month', current_date())) as months_ago,
        
        -- Quarters ago calculation
        datediff('quarter', date_month, date_trunc('quarter', current_date())) as quarters_ago,
        
        -- Years ago calculation
        datediff('year', date_month, date_trunc('year', current_date())) as years_ago,
        
        -- Business day indicators (first/last month)
        date_month = date_trunc('month', date_month) as is_first_day_of_month,
        date_month = last_day(date_month) as is_last_day_of_month,
        
        -- Season classification
        case 
            when month(date_month) in (12, 1, 2) then 'Winter'
            when month(date_month) in (3, 4, 5) then 'Spring'
            when month(date_month) in (6, 7, 8) then 'Summer'
            when month(date_month) in (9, 10, 11) then 'Fall'
        end as season,
        
        -- Useful for rent seasonality analysis
        case
            when month(date_month) in (5, 6, 7, 8) then 'Peak Moving Season'
            when month(date_month) in (11, 12, 1) then 'Low Moving Season'
            else 'Normal Season'
        end as rental_season,
        
        -- Data lineage
        current_timestamp() as created_at,
        '{{ run_started_at }}' as dbt_run_id
        
    from date_spine
)

select * from calendar_attributes
order by time_key