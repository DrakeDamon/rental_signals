"""Freshness asset checks for Tampa Rent Signals pipeline."""

from datetime import datetime, timedelta
from dagster import (
    asset_check,
    AssetCheckResult,
    AssetExecutionContext,
    AssetCheckSeverity,
    MetadataValue,
)
from dagster_snowflake import SnowflakeResource


@asset_check(
    asset=["staging", "stg_aptlist"],
    description="Check data freshness for ApartmentList staging data",
)
def stg_aptlist_freshness_check(
    context: AssetExecutionContext, 
    snowflake: SnowflakeResource
) -> AssetCheckResult:
    """
    Check that ApartmentList staging data is fresh (< 24 hours old).
    """
    try:
        with snowflake.get_connection() as conn:
            query = """
            SELECT MAX(month_date) as latest_date,
                   DATEDIFF('hour', MAX(month_date), CURRENT_TIMESTAMP()) as hours_old
            FROM rents.staging.stg_aptlist
            """
            
            result = conn.execute(query).fetchone()
            latest_date = result[0] if result else None
            hours_old = result[1] if result else None
            
            metadata = {
                "latest_date": MetadataValue.text(str(latest_date)),
                "hours_old": MetadataValue.int(hours_old) if hours_old else MetadataValue.text("Unknown"),
            }
            
            if hours_old is None:
                return AssetCheckResult(
                    passed=False,
                    description="No data found in staging table",
                    metadata=metadata,
                    severity=AssetCheckSeverity.ERROR,
                )
            elif hours_old <= 24:
                return AssetCheckResult(
                    passed=True,
                    description=f"Data is fresh ({hours_old} hours old)",
                    metadata=metadata,
                )
            else:
                return AssetCheckResult(
                    passed=False,
                    description=f"Data is stale ({hours_old} hours old, should be < 24 hours)",
                    metadata=metadata,
                    severity=AssetCheckSeverity.WARN,
                )
                
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to check freshness: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["staging", "stg_zori"],
    description="Check data freshness for Zillow ZORI staging data",
)
def stg_zori_freshness_check(
    context: AssetExecutionContext,
    snowflake: SnowflakeResource
) -> AssetCheckResult:
    """
    Check that Zillow ZORI staging data is fresh (< 24 hours old).
    """
    try:
        with snowflake.get_connection() as conn:
            query = """
            SELECT MAX(month_date) as latest_date,
                   DATEDIFF('hour', MAX(month_date), CURRENT_TIMESTAMP()) as hours_old
            FROM rents.staging.stg_zori
            """
            
            result = conn.execute(query).fetchone()
            latest_date = result[0] if result else None
            hours_old = result[1] if result else None
            
            metadata = {
                "latest_date": MetadataValue.text(str(latest_date)),
                "hours_old": MetadataValue.int(hours_old) if hours_old else MetadataValue.text("Unknown"),
            }
            
            if hours_old is None:
                return AssetCheckResult(
                    passed=False,
                    description="No data found in staging table",
                    metadata=metadata,
                    severity=AssetCheckSeverity.ERROR,
                )
            elif hours_old <= 24:
                return AssetCheckResult(
                    passed=True,
                    description=f"Data is fresh ({hours_old} hours old)",
                    metadata=metadata,
                )
            else:
                return AssetCheckResult(
                    passed=False,
                    description=f"Data is stale ({hours_old} hours old, should be < 24 hours)",
                    metadata=metadata,
                    severity=AssetCheckSeverity.WARN,
                )
                
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to check freshness: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["staging", "stg_fred"],
    description="Check data freshness for FRED economic staging data",
)
def stg_fred_freshness_check(
    context: AssetExecutionContext,
    snowflake: SnowflakeResource
) -> AssetCheckResult:
    """
    Check that FRED economic staging data is fresh (< 24 hours old).
    """
    try:
        with snowflake.get_connection() as conn:
            query = """
            SELECT MAX(month_date) as latest_date,
                   DATEDIFF('hour', MAX(month_date), CURRENT_TIMESTAMP()) as hours_old
            FROM rents.staging.stg_fred
            """
            
            result = conn.execute(query).fetchone()
            latest_date = result[0] if result else None
            hours_old = result[1] if result else None
            
            metadata = {
                "latest_date": MetadataValue.text(str(latest_date)),
                "hours_old": MetadataValue.int(hours_old) if hours_old else MetadataValue.text("Unknown"),
            }
            
            if hours_old is None:
                return AssetCheckResult(
                    passed=False,
                    description="No data found in staging table",
                    metadata=metadata,
                    severity=AssetCheckSeverity.ERROR,
                )
            elif hours_old <= 24:
                return AssetCheckResult(
                    passed=True,
                    description=f"Data is fresh ({hours_old} hours old)",
                    metadata=metadata,
                )
            else:
                return AssetCheckResult(
                    passed=False,
                    description=f"Data is stale ({hours_old} hours old, should be < 24 hours)",
                    metadata=metadata,
                    severity=AssetCheckSeverity.WARN,
                )
                
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to check freshness: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["marts", "mart_rent_trends"],
    description="Check data freshness for mart_rent_trends",
)
def mart_rent_trends_freshness_check(
    context: AssetExecutionContext,
    snowflake: SnowflakeResource
) -> AssetCheckResult:
    """
    Check that mart_rent_trends data is reasonably fresh (< 72 hours old).
    """
    try:
        with snowflake.get_connection() as conn:
            query = """
            SELECT MAX(month_date) as latest_date,
                   DATEDIFF('hour', MAX(month_date), CURRENT_TIMESTAMP()) as hours_old
            FROM rents.marts.mart_rent_trends
            """
            
            result = conn.execute(query).fetchone()
            latest_date = result[0] if result else None
            hours_old = result[1] if result else None
            
            metadata = {
                "latest_date": MetadataValue.text(str(latest_date)),
                "hours_old": MetadataValue.int(hours_old) if hours_old else MetadataValue.text("Unknown"),
            }
            
            if hours_old is None:
                return AssetCheckResult(
                    passed=False,
                    description="No data found in mart table",
                    metadata=metadata,
                    severity=AssetCheckSeverity.ERROR,
                )
            elif hours_old <= 72:  # More lenient for marts
                return AssetCheckResult(
                    passed=True,
                    description=f"Data is fresh ({hours_old} hours old)",
                    metadata=metadata,
                )
            else:
                return AssetCheckResult(
                    passed=False,
                    description=f"Data is stale ({hours_old} hours old, should be < 72 hours)",
                    metadata=metadata,
                    severity=AssetCheckSeverity.WARN,
                )
                
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to check freshness: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


# Collect all freshness checks
freshness_checks = [
    stg_aptlist_freshness_check,
    stg_zori_freshness_check,
    stg_fred_freshness_check,
    mart_rent_trends_freshness_check,
]