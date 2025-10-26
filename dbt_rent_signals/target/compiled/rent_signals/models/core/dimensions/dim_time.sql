

with date_spine as (
    





with rawdata as (

    

    

    with p as (
        select 0 as generated_number union all select 1
    ), unioned as (

    select

    
    p0.generated_number * power(2, 0)
     + 
    
    p1.generated_number * power(2, 1)
     + 
    
    p2.generated_number * power(2, 2)
     + 
    
    p3.generated_number * power(2, 3)
     + 
    
    p4.generated_number * power(2, 4)
     + 
    
    p5.generated_number * power(2, 5)
     + 
    
    p6.generated_number * power(2, 6)
     + 
    
    p7.generated_number * power(2, 7)
    
    
    + 1
    as generated_number

    from

    
    p as p0
     cross join 
    
    p as p1
     cross join 
    
    p as p2
     cross join 
    
    p as p3
     cross join 
    
    p as p4
     cross join 
    
    p as p5
     cross join 
    
    p as p6
     cross join 
    
    p as p7
    
    

    )

    select *
    from unioned
    where generated_number <= 191
    order by generated_number



),

all_periods as (

    select (
        

    dateadd(
        month,
        row_number() over (order by 1) - 1,
        to_date('2015-01-01', 'yyyy-mm-dd')
        )


    ) as date_month
    from rawdata

),

filtered as (

    select *
    from all_periods
    where date_month <= to_date('2030-12-31', 'yyyy-mm-dd')

)

select * from filtered


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
        '2025-10-26 04:07:02.967691+00:00' as dbt_run_id
        
    from date_spine
)

select * from calendar_attributes
order by time_key