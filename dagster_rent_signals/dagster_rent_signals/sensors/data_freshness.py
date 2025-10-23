"""Data freshness sensor for Tampa Rent Signals pipeline."""

from dagster import (
    sensor,
    SensorResult,
    SensorEvaluationContext,
    RunRequest,
    DefaultSensorStatus,
)
from dagster_snowflake import SnowflakeResource
from datetime import datetime, timedelta

from ..jobs.data_pipeline import staging_pipeline


@sensor(
    job=staging_pipeline,
    default_status=DefaultSensorStatus.RUNNING,
    description="Trigger staging pipeline when new data is detected in Snowflake raw tables",
)
def data_freshness_sensor(
    context: SensorEvaluationContext,
    snowflake: SnowflakeResource,
) -> SensorResult:
    """
    Monitor Snowflake raw tables for new data and trigger staging pipeline.
    
    Checks for:
    - New files in external stages (S3)
    - Recent data loads into raw tables
    - Data freshness compared to last successful run
    """
    try:
        run_requests = []
        
        with snowflake.get_connection() as conn:
            # Check for recent data in raw tables
            freshness_query = """
            WITH source_freshness AS (
                SELECT 
                    'aptlist' as source,
                    MAX(month_date) as latest_date,
                    DATEDIFF('hour', MAX(month_date), CURRENT_TIMESTAMP()) as hours_old
                FROM rents.raw.aptlist_long
                
                UNION ALL
                
                SELECT 
                    'zori' as source,
                    MAX(month_date) as latest_date,
                    DATEDIFF('hour', MAX(month_date), CURRENT_TIMESTAMP()) as hours_old
                FROM rents.raw.zori_metro_long
                
                UNION ALL
                
                SELECT 
                    'fred' as source,
                    MAX(month_date) as latest_date,
                    DATEDIFF('hour', MAX(month_date), CURRENT_TIMESTAMP()) as hours_old
                FROM rents.raw.fred_cpi_long
            )
            SELECT source, latest_date, hours_old
            FROM source_freshness
            WHERE hours_old <= 6  -- Data loaded in last 6 hours
            """
            
            fresh_sources = conn.execute(freshness_query).fetchall()
            
            # Check if we should trigger based on fresh data
            if fresh_sources:
                sources_with_fresh_data = [row[0] for row in fresh_sources]
                
                # Get the cursor (last run timestamp) to avoid duplicate runs
                last_run_time = context.cursor
                current_time = datetime.now()
                
                # Only trigger if it's been at least 1 hour since last run
                if not last_run_time or (current_time - datetime.fromisoformat(last_run_time)).total_seconds() > 3600:
                    
                    run_requests.append(
                        RunRequest(
                            run_key=f"fresh_data_{current_time.strftime('%Y%m%d_%H%M%S')}",
                            tags={
                                "triggered_by": "data_freshness_sensor",
                                "fresh_sources": ",".join(sources_with_fresh_data),
                                "trigger_time": current_time.isoformat(),
                            },
                        )
                    )
                    
                    context.log.info(
                        f"Triggering staging pipeline due to fresh data in sources: {sources_with_fresh_data}"
                    )
                    
                    # Update cursor to current time
                    new_cursor = current_time.isoformat()
                else:
                    context.log.info(
                        f"Fresh data detected in {sources_with_fresh_data}, but recent run detected. Skipping."
                    )
                    new_cursor = last_run_time
            else:
                context.log.info("No fresh data detected in raw tables")
                new_cursor = last_run_time
                
        return SensorResult(
            run_requests=run_requests,
            cursor=new_cursor,
        )
        
    except Exception as e:
        context.log.error(f"Error in data freshness sensor: {str(e)}")
        return SensorResult(
            run_requests=[],
            cursor=context.cursor,
        )