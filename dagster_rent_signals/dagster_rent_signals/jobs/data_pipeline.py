"""Pipeline job definitions for Tampa Rent Signals."""

from dagster import (
    define_asset_job,
    AssetSelection,
    DefaultSensorStatus,
)


# Staging pipeline - process raw data into staging models
staging_pipeline = define_asset_job(
    name="staging_pipeline",
    description="Process raw data into staging models with data quality validation",
    selection=AssetSelection.groups("staging"),
    tags={
        "layer": "staging",
        "dagster/priority": "high",
        "team": "data_engineering",
    },
)


# Core pipeline - build star schema from staging data
core_pipeline = define_asset_job(
    name="core_pipeline", 
    description="Build core star schema (dimensions and facts) from staging data",
    selection=AssetSelection.groups("core_dimensions", "core_facts", "snapshots"),
    tags={
        "layer": "core",
        "dagster/priority": "high", 
        "team": "data_engineering",
    },
)


# Marts pipeline - create business-ready analytics
marts_pipeline = define_asset_job(
    name="marts_pipeline",
    description="Create business-ready mart models for analytics and reporting",
    selection=AssetSelection.groups("marts_analytics", "marts_summaries"),
    tags={
        "layer": "marts",
        "dagster/priority": "medium",
        "team": "analytics",
    },
)


# Full refresh pipeline - complete end-to-end refresh
full_refresh_pipeline = define_asset_job(
    name="full_refresh_pipeline",
    description="Complete end-to-end pipeline refresh from staging to marts",
    selection=AssetSelection.all(),
    tags={
        "dagster/priority": "medium",
        "team": "data_engineering",
        "pipeline_type": "full_refresh",
    },
)