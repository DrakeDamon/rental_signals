"""dbt resource configuration for Tampa Rent Signals pipeline."""

import os
from pathlib import Path
from dagster import EnvVar
from dagster_dbt import DbtCliResource

# Get the absolute path to the dbt project
DBT_PROJECT_DIR = Path(__file__).parent.parent.parent.parent / "dbt_rent_signals"

dbt_resource = DbtCliResource(
    project_dir=str(DBT_PROJECT_DIR),
    profiles_dir=str(DBT_PROJECT_DIR),
    target="prod",  # Can be overridden with environment variable
    global_config_flags=[
        "--no-write-json",  # Prevent writing to logs
        "--no-version-check",  # Skip version checks for faster execution
    ],
)