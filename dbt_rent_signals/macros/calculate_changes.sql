-- Macro to calculate year-over-year and month-over-month changes
{% macro calculate_changes(value_column, partition_by, order_by='s.month_date') %}
    -- Year-over-year changes
    {{ value_column }} - lag({{ value_column }}, 12) over (
        partition by {{ partition_by }}
        order by {{ order_by }}
    ) as yoy_change,
    
    round(
        ({{ value_column }} - lag({{ value_column }}, 12) over (
            partition by {{ partition_by }}
            order by {{ order_by }}
        )) / nullif(lag({{ value_column }}, 12) over (
            partition by {{ partition_by }}
            order by {{ order_by }}
        ), 0) * 100, 
        2
    ) as yoy_pct_change,
    
    -- Month-over-month changes
    {{ value_column }} - lag({{ value_column }}, 1) over (
        partition by {{ partition_by }}
        order by {{ order_by }}
    ) as mom_change,
    
    round(
        ({{ value_column }} - lag({{ value_column }}, 1) over (
            partition by {{ partition_by }}
            order by {{ order_by }}
        )) / nullif(lag({{ value_column }}, 1) over (
            partition by {{ partition_by }}
            order by {{ order_by }}
        ), 0) * 100, 
        2
    ) as mom_pct_change
{% endmacro %}