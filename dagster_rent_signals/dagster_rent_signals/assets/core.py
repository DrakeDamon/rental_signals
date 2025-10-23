"""Core layer assets for Tampa Rent Signals pipeline."""

from dagster import (
    asset,
    AssetExecutionContext,
    AssetIn,
    FreshnessPolicy,
    MetadataValue,
    Output,
)
from dagster_dbt import DbtCliResource
from typing import Any, Mapping


@asset(
    key=["core", "dim_time"],
    description="Calendar dimension table with date hierarchy for time-series analysis",
    group_name="core_dimensions",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 48),  # 48 hours
    metadata={
        "layer": "core",
        "type": "dimension",
        "dbt_model": "dim_time",
        "scd_type": "static",
    },
)
def dim_time(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Calendar dimension with comprehensive date attributes.
    
    Features:
    - Monthly grain for rent time series
    - Quarter and year rollups
    - Current period flags
    - Business date calculations
    """
    dbt_build_result = dbt.cli(["run", "--select", "dim_time"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "dim_time"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["core", "dim_data_source"],
    description="Static reference dimension for data sources with reliability scoring",
    group_name="core_dimensions",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 48),  # 48 hours
    metadata={
        "layer": "core",
        "type": "dimension",
        "dbt_model": "dim_data_source",
        "scd_type": "static",
    },
)
def dim_data_source(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Static data source reference dimension.
    
    Features:
    - Source system metadata
    - Data type classifications
    - Reliability scoring (1-10)
    - Update frequency information
    """
    dbt_build_result = dbt.cli(["run", "--select", "dim_data_source"], context=context)
    
    # Extract metadata from dbt run results  
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "dim_data_source"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["core", "fact_rent_zori"],
    ins={
        "stg_zori": AssetIn(["staging", "stg_zori"]),
        "dim_time": AssetIn(["core", "dim_time"]),
        "dim_data_source": AssetIn(["core", "dim_data_source"]),
    },
    description="Zillow ZORI rent facts with calculated YoY/MoM measures and investment scoring",
    group_name="core_facts",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 48),  # 48 hours
    metadata={
        "layer": "core",
        "type": "fact",
        "dbt_model": "fact_rent_zori",
        "grain": "regionid, month_date",
    },
)
def fact_rent_zori(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Zillow ZORI rent fact table with sophisticated business calculations.
    
    Features:
    - YoY and MoM change calculations
    - National ranking and percentiles
    - Growth category classification
    - Investment attractiveness scoring
    - Data quality and anomaly detection
    """
    dbt_build_result = dbt.cli(["run", "--select", "fact_rent_zori"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "fact_rent_zori"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["core", "fact_rent_aptlist"],
    ins={
        "stg_aptlist": AssetIn(["staging", "stg_aptlist"]),
        "dim_time": AssetIn(["core", "dim_time"]),
        "dim_data_source": AssetIn(["core", "dim_data_source"]),
    },
    description="ApartmentList rent facts with population-based analytics and market classification",
    group_name="core_facts",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 48),  # 48 hours
    metadata={
        "layer": "core",
        "type": "fact",
        "dbt_model": "fact_rent_aptlist",
        "grain": "location_fips_code, month_date",
    },
)
def fact_rent_aptlist(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    ApartmentList rent fact table with population-based market analytics.
    
    Features:
    - Population-weighted rent calculations
    - Market size categorization
    - YoY and MoM trend analysis
    - Geographic clustering analysis
    - Cross-reference validation with ZORI data
    """
    dbt_build_result = dbt.cli(["run", "--select", "fact_rent_aptlist"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "fact_rent_aptlist"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["core", "fact_economic_indicator"],
    ins={
        "stg_fred": AssetIn(["staging", "stg_fred"]),
        "dim_time": AssetIn(["core", "dim_time"]),
        "dim_data_source": AssetIn(["core", "dim_data_source"]),
    },
    description="Federal Reserve economic indicator facts with trend analysis and policy implications",
    group_name="core_facts",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 48),  # 48 hours
    metadata={
        "layer": "core",
        "type": "fact",
        "dbt_model": "fact_economic_indicator",
        "grain": "series_id, month_date",
    },
)
def fact_economic_indicator(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Economic indicator fact table with comprehensive trend analysis.
    
    Features:
    - CPI and inflation calculations
    - YoY and MoM economic growth
    - Seasonal adjustment handling
    - Policy regime classification
    - Correlation with housing markets
    """
    dbt_build_result = dbt.cli(["run", "--select", "fact_economic_indicator"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "fact_economic_indicator"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


# Collect all core assets
core_assets = [
    dim_time,
    dim_data_source, 
    fact_rent_zori,
    fact_rent_aptlist,
    fact_economic_indicator,
]