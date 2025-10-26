-- Macro for standardized data quality scoring
{% macro data_quality_score(value_column, min_value=0, max_value=null, required_columns=[]) %}
    case
        {% for col in required_columns %}
        when {{ col }} is null then 1
        {% endfor %}
        when {{ value_column }} is null then 2
        when {{ value_column }} < {{ min_value }} then 3
        {% if max_value %}
        when {{ value_column }} > {{ max_value }} then 4
        {% endif %}
        else 10
    end
{% endmacro %}

-- Macro for anomaly detection using statistical methods
{% macro detect_anomalies(value_column, partition_by, window_size=5, std_dev_threshold=2) %}
    case
        when abs({{ value_column }} - avg({{ value_column }}) over (
            partition by {{ partition_by }}
            order by s.month_date
            rows between {{ window_size }} preceding and {{ window_size }} following
        )) > {{ std_dev_threshold }} * stddev({{ value_column }}) over (
            partition by {{ partition_by }}
            order by s.month_date
            rows between {{ window_size }} preceding and {{ window_size }} following
        ) then true
        else false
    end
{% endmacro %}