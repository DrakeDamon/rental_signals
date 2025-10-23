"""Snapshot assets for SCD Type 2 historical tracking."""

from dagster import (
    asset,
    AssetExecutionContext,
    AssetIn,
    FreshnessPolicy,
    MetadataValue,
    Output,
)
from dagster_dbt import DbtCliResource


@asset(
    key=["snapshots", "snap_location"],
    ins={
        "stg_aptlist": AssetIn(["staging", "stg_aptlist"]),
        "stg_zori": AssetIn(["staging", "stg_zori"]),
    },
    description="Location dimension with SCD Type 2 historical tracking using hash-based change detection",
    group_name="snapshots",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 48),  # 48 hours
    metadata={
        "layer": "snapshots",
        "type": "scd_type_2",
        "dbt_model": "snap_location",
        "change_strategy": "check",
    },
)
def snap_location(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Location dimension snapshot with SCD Type 2 tracking.
    
    Features:
    - Hash-based change detection for location attributes
    - Effective and end date management
    - Current record flagging
    - Geographic hierarchy preservation
    - Population and demographic tracking over time
    """
    dbt_build_result = dbt.cli(["snapshot", "--select", "snap_location"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "snap_location"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("snapshot"),
            "strategy": MetadataValue.text("check"),
            "check_cols": MetadataValue.text("location_content_hash"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["snapshots", "snap_economic_series"],
    ins={
        "stg_fred": AssetIn(["staging", "stg_fred"]),
    },
    description="Economic series dimension with SCD Type 2 tracking for metadata changes",
    group_name="snapshots", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 48),  # 48 hours
    metadata={
        "layer": "snapshots",
        "type": "scd_type_2",
        "dbt_model": "snap_economic_series",
        "change_strategy": "check",
    },
)
def snap_economic_series(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Economic series dimension snapshot with SCD Type 2 tracking.
    
    Features:
    - FRED series metadata change tracking
    - Category and frequency evolution
    - Label and description updates
    - Seasonal adjustment modifications
    - Data revision history
    """
    dbt_build_result = dbt.cli(["snapshot", "--select", "snap_economic_series"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "snap_economic_series"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("snapshot"),
            "strategy": MetadataValue.text("check"),
            "check_cols": MetadataValue.text("series_content_hash"),
        })
    
    return Output(None, metadata=metadata)


# Create dimension assets that depend on snapshots
@asset(
    key=["core", "dim_location"],
    ins={
        "snap_location": AssetIn(["snapshots", "snap_location"]),
    },
    description="Current and historical location dimension derived from SCD Type 2 snapshot",
    group_name="core_dimensions",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 48),  # 48 hours
    metadata={
        "layer": "core",
        "type": "dimension",
        "dbt_model": "dim_location",
        "scd_type": "type_2",
    },
)
def dim_location(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Location dimension table derived from SCD Type 2 snapshot.
    
    Features:
    - Current and historical location records
    - Geographic hierarchy (state, county, metro)
    - Population and demographic attributes
    - Business key for cross-referencing
    - Effective date ranges for time travel queries
    """
    dbt_build_result = dbt.cli(["run", "--select", "dim_location"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "dim_location"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["core", "dim_economic_series"],
    ins={
        "snap_economic_series": AssetIn(["snapshots", "snap_economic_series"]),
    },
    description="Current and historical economic series dimension derived from SCD Type 2 snapshot",
    group_name="core_dimensions",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 48),  # 48 hours
    metadata={
        "layer": "core",
        "type": "dimension",
        "dbt_model": "dim_economic_series",
        "scd_type": "type_2",
    },
)
def dim_economic_series(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Economic series dimension table derived from SCD Type 2 snapshot.
    
    Features:
    - FRED series metadata with historical changes
    - Category and frequency tracking
    - Seasonal adjustment evolution
    - Data revision tracking
    - Effective date ranges for analysis
    """
    dbt_build_result = dbt.cli(["run", "--select", "dim_economic_series"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "dim_economic_series"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


# Collect all snapshot-related assets
snapshot_assets = [
    snap_location,
    snap_economic_series,
    dim_location,
    dim_economic_series,
]