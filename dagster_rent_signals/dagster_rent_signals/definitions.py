"""Main Dagster definitions for Tampa Rent Signals pipeline."""

from dagster import Definitions

from .assets import (
    staging_assets,
    core_assets,
    mart_assets,
    snapshot_assets,
)
from .resources import (
    dbt_resource,
    snowflake_io_manager,
    great_expectations_resource,
)
from .jobs import (
    staging_pipeline,
    core_pipeline,
    marts_pipeline,
    full_refresh_pipeline,
)
from .schedules import (
    daily_refresh_schedule,
    weekly_validation_schedule,
)
from .sensors import (
    data_freshness_sensor,
)
from .checks import (
    freshness_checks,
    quality_checks,
    business_rule_checks,
)

# Combine all assets
all_assets = [
    *staging_assets,
    *core_assets,
    *mart_assets,
    *snapshot_assets,
]

# Combine all checks
all_checks = [
    *freshness_checks,
    *quality_checks,
    *business_rule_checks,
]

# Define the complete Dagster definitions
defs = Definitions(
    assets=all_assets,
    asset_checks=all_checks,
    jobs=[
        staging_pipeline,
        core_pipeline,
        marts_pipeline,
        full_refresh_pipeline,
    ],
    schedules=[
        daily_refresh_schedule,
        weekly_validation_schedule,
    ],
    sensors=[
        data_freshness_sensor,
    ],
    resources={
        "dbt": dbt_resource,
        "snowflake_io_manager": snowflake_io_manager,
        "snowflake": snowflake_io_manager,  # Alias for asset checks
        "great_expectations": great_expectations_resource,
    },
)