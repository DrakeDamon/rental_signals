"""Snowflake resource configuration for Tampa Rent Signals pipeline."""

import os
from dagster import EnvVar
from dagster_snowflake import SnowflakeIOManager

snowflake_io_manager = SnowflakeIOManager(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    database=EnvVar("SNOWFLAKE_DATABASE"),
    warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
    role=EnvVar("SNOWFLAKE_ROLE"),
    schema=EnvVar("SNOWFLAKE_SCHEMA"),
)