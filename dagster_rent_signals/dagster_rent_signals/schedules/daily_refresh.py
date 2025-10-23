"""Schedule definitions for Tampa Rent Signals pipeline."""

from dagster import (
    ScheduleDefinition,
    DefaultScheduleStatus,
    RunRequest,
    ScheduleEvaluationContext,
)

from ..jobs.data_pipeline import full_refresh_pipeline, staging_pipeline


# Daily staging refresh at 6 AM EST
daily_refresh_schedule = ScheduleDefinition(
    job=staging_pipeline,
    cron_schedule="0 6 * * *",  # 6 AM EST daily
    default_status=DefaultScheduleStatus.RUNNING,
    description="Daily refresh of staging models at 6 AM EST",
    tags={
        "schedule_type": "daily",
        "pipeline_layer": "staging",
        "priority": "high",
    },
)


# Weekly full pipeline refresh on Sundays at 2 AM EST
weekly_validation_schedule = ScheduleDefinition(
    job=full_refresh_pipeline,
    cron_schedule="0 2 * * 0",  # 2 AM EST every Sunday
    default_status=DefaultScheduleStatus.RUNNING,
    description="Weekly full pipeline refresh and comprehensive validation",
    tags={
        "schedule_type": "weekly",
        "pipeline_layer": "full",
        "priority": "medium",
    },
)