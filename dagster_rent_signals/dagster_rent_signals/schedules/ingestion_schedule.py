"""Schedules for data ingestion assets."""

from dagster import (
    ScheduleDefinition,
    DefaultScheduleStatus,
    define_asset_job,
)

from ..assets.ingestion import ingestion_assets

# Define a job for monthly ingestion
monthly_ingestion_job = define_asset_job(
    name="monthly_ingestion_job",
    selection=[asset.key for asset in ingestion_assets],
    description="Monthly data ingestion from all sources (Zillow, ApartmentList, FRED)",
)

# Schedule to run on the 2nd day of each month at 3 AM EST
# Data typically updates on the 1st, so we run on the 2nd to ensure availability
monthly_ingestion_schedule = ScheduleDefinition(
    name="monthly_ingestion_schedule",
    job=monthly_ingestion_job,
    cron_schedule="0 3 2 * *",  # 3 AM on the 2nd day of every month
    execution_timezone="America/New_York",
    default_status=DefaultScheduleStatus.RUNNING,
    description="Run data ingestion monthly on the 2nd day at 3 AM EST",
)

