-- Macro to create SCD Type 2 indexes on dimension tables
{% macro create_scd2_indexes() %}
    {% if target.name == 'prod' %}
        {% set indexes = [
            "create index if not exists idx_" ~ this.identifier ~ "_current on " ~ this ~ "(is_current)",
            "create index if not exists idx_" ~ this.identifier ~ "_effective_date on " ~ this ~ "(effective_date, end_date)",
            "create index if not exists idx_" ~ this.identifier ~ "_business_key on " ~ this ~ "(location_business_key)" if 'location' in this.identifier else "create index if not exists idx_" ~ this.identifier ~ "_business_key on " ~ this ~ "(series_business_key)"
        ] %}
        
        {% for index_sql in indexes %}
            {{ index_sql }};
        {% endfor %}
    {% endif %}
{% endmacro %}

-- Macro to create fact table indexes and clustering
{% macro create_fact_indexes() %}
    {% if target.name == 'prod' %}
        {% set cluster_sql = "alter table " ~ this ~ " cluster by (time_key, location_key)" %}
        {{ cluster_sql }};
    {% endif %}
{% endmacro %}