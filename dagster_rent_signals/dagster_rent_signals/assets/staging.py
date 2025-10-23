"""Staging layer assets for Tampa Rent Signals pipeline."""

from dagster import (
    asset,
    AssetExecutionContext,
    FreshnessPolicy,
    MetadataValue,
    Output,
)
from dagster_dbt import DbtCliResource, dbt_assets, get_asset_key_for_model
from typing import Any, Mapping

from ..resources.dbt import DBT_PROJECT_DIR


@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    select="tag:layer:staging",
)
def staging_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """
    Software-defined assets for staging layer models.
    
    Includes:
    - stg_aptlist: ApartmentList rent data with data quality scoring
    - stg_zori: Zillow ZORI rent data with metro categorization
    - stg_fred: Federal Reserve economic data with series validation
    """
    yield from dbt.cli(["build", "--select", "tag:layer:staging"], context=context).stream()


@asset(
    key=["staging", "stg_aptlist"],
    description="Cleaned and standardized ApartmentList rent data from raw CSV imports",
    group_name="staging",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 24),  # 24 hours
    metadata={
        "source": "ApartmentList",
        "layer": "staging", 
        "dbt_model": "stg_aptlist",
        "data_type": "rent_estimates",
    },
)
def stg_aptlist(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    ApartmentList staging model with data quality scoring and standardization.
    
    Features:
    - Business key generation for location tracking
    - Data quality scoring (1-10 scale)
    - Population and geographic standardization
    - Anomaly detection for rent values
    """
    dbt_build_result = dbt.cli(["run", "--select", "stg_aptlist"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "stg_aptlist"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("view"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["staging", "stg_zori"],
    description="Cleaned and standardized Zillow ZORI rent data with metro size categorization",
    group_name="staging",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 24),  # 24 hours
    metadata={
        "source": "Zillow",
        "layer": "staging",
        "dbt_model": "stg_zori", 
        "data_type": "rent_index",
    },
)
def stg_zori(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Zillow ZORI staging model with metro size categorization and quality controls.
    
    Features:
    - Metro size classification (Major, Large, Medium, Small)
    - ZORI value validation and range checking
    - State name standardization
    - Size rank validation for consistency
    """
    dbt_build_result = dbt.cli(["run", "--select", "stg_zori"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "stg_zori"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("view"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["staging", "stg_fred"],
    description="Cleaned and standardized Federal Reserve economic data with series validation",
    group_name="staging",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 24),  # 24 hours
    metadata={
        "source": "FRED",
        "layer": "staging",
        "dbt_model": "stg_fred",
        "data_type": "economic_indicators",
    },
)
def stg_fred(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Federal Reserve economic data staging model with series validation.
    
    Features:
    - FRED series ID validation and formatting
    - CPI category classification
    - Seasonal adjustment detection
    - Economic indicator value range validation
    """
    dbt_build_result = dbt.cli(["run", "--select", "stg_fred"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "stg_fred"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("view"),
        })
    
    return Output(None, metadata=metadata)


# Collect all staging assets
staging_assets = [stg_aptlist, stg_zori, stg_fred]