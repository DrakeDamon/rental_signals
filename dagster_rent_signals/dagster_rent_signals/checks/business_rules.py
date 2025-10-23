"""Business rule asset checks for Tampa Rent Signals pipeline."""

from dagster import (
    asset_check,
    AssetCheckResult,
    AssetExecutionContext,
    AssetCheckSeverity,
    MetadataValue,
)
from dagster_snowflake import SnowflakeResource


@asset_check(
    asset=["core", "fact_rent_zori"],
    description="Check that YoY rent growth is within reasonable bounds",
)
def zori_growth_bounds_check(
    context: AssetExecutionContext,
    snowflake: SnowflakeResource
) -> AssetCheckResult:
    """
    Check that year-over-year rent growth is within reasonable bounds (-50% to +100%).
    Extreme values may indicate data quality issues.
    """
    try:
        with snowflake.get_connection() as conn:
            query = """
            SELECT COUNT(*) as total_records,
                   COUNT(CASE WHEN yoy_pct_change < -50 OR yoy_pct_change > 100 
                         THEN 1 END) as outlier_records,
                   MIN(yoy_pct_change) as min_yoy_change,
                   MAX(yoy_pct_change) as max_yoy_change,
                   AVG(yoy_pct_change) as avg_yoy_change
            FROM rents.core.fact_rent_zori
            WHERE yoy_pct_change IS NOT NULL
            """
            
            result = conn.execute(query).fetchone()
            total_records = result[0]
            outlier_records = result[1]
            min_yoy = result[2]
            max_yoy = result[3]
            avg_yoy = result[4]
            
            outlier_pct = (outlier_records / total_records * 100) if total_records > 0 else 0
            
            metadata = {
                "total_records": MetadataValue.int(total_records),
                "outlier_records": MetadataValue.int(outlier_records),
                "outlier_percentage": MetadataValue.float(outlier_pct),
                "min_yoy_change": MetadataValue.float(min_yoy) if min_yoy else MetadataValue.text("N/A"),
                "max_yoy_change": MetadataValue.float(max_yoy) if max_yoy else MetadataValue.text("N/A"),
                "avg_yoy_change": MetadataValue.float(avg_yoy) if avg_yoy else MetadataValue.text("N/A"),
            }
            
            if outlier_pct <= 1.0:  # Allow up to 1% outliers
                return AssetCheckResult(
                    passed=True,
                    description=f"YoY growth within bounds ({outlier_pct:.2f}% outliers)",
                    metadata=metadata,
                )
            else:
                severity = AssetCheckSeverity.WARN if outlier_pct <= 5.0 else AssetCheckSeverity.ERROR
                return AssetCheckResult(
                    passed=False,
                    description=f"Too many YoY growth outliers ({outlier_pct:.2f}% of records)",
                    metadata=metadata,
                    severity=severity,
                )
                
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to check YoY growth bounds: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["core", "fact_rent_aptlist"],
    description="Check that population values are positive and reasonable",
)
def aptlist_population_check(
    context: AssetExecutionContext,
    snowflake: SnowflakeResource
) -> AssetCheckResult:
    """
    Check that population values in ApartmentList data are positive and within reasonable ranges.
    """
    try:
        with snowflake.get_connection() as conn:
            query = """
            SELECT COUNT(*) as total_records,
                   COUNT(CASE WHEN population <= 0 THEN 1 END) as invalid_population,
                   COUNT(CASE WHEN population > 50000000 THEN 1 END) as unrealistic_population,
                   MIN(population) as min_population,
                   MAX(population) as max_population,
                   AVG(population) as avg_population
            FROM rents.core.fact_rent_aptlist
            WHERE population IS NOT NULL
            """
            
            result = conn.execute(query).fetchone()
            total_records = result[0]
            invalid_pop = result[1]
            unrealistic_pop = result[2]
            min_pop = result[3]
            max_pop = result[4]
            avg_pop = result[5]
            
            invalid_pct = (invalid_pop / total_records * 100) if total_records > 0 else 0
            unrealistic_pct = (unrealistic_pop / total_records * 100) if total_records > 0 else 0
            
            metadata = {
                "total_records": MetadataValue.int(total_records),
                "invalid_population_records": MetadataValue.int(invalid_pop),
                "unrealistic_population_records": MetadataValue.int(unrealistic_pop),
                "invalid_percentage": MetadataValue.float(invalid_pct),
                "unrealistic_percentage": MetadataValue.float(unrealistic_pct),
                "min_population": MetadataValue.int(min_pop) if min_pop else MetadataValue.text("N/A"),
                "max_population": MetadataValue.int(max_pop) if max_pop else MetadataValue.text("N/A"),
                "avg_population": MetadataValue.float(avg_pop) if avg_pop else MetadataValue.text("N/A"),
            }
            
            if invalid_pct == 0 and unrealistic_pct <= 0.1:  # Allow 0.1% unrealistic values
                return AssetCheckResult(
                    passed=True,
                    description="Population values are valid and reasonable",
                    metadata=metadata,
                )
            else:
                return AssetCheckResult(
                    passed=False,
                    description=f"Invalid population data: {invalid_pct:.2f}% invalid, {unrealistic_pct:.2f}% unrealistic",
                    metadata=metadata,
                    severity=AssetCheckSeverity.WARN,
                )
                
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to check population values: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["marts", "mart_rent_trends"],
    description="Check data completeness for key business metrics",
)
def rent_trends_completeness_check(
    context: AssetExecutionContext,
    snowflake: SnowflakeResource
) -> AssetCheckResult:
    """
    Check that key business metrics in mart_rent_trends have acceptable completeness.
    """
    try:
        with snowflake.get_connection() as conn:
            query = """
            SELECT COUNT(*) as total_records,
                   COUNT(CASE WHEN yoy_pct_change IS NULL THEN 1 END) as missing_yoy,
                   COUNT(CASE WHEN investment_attractiveness_score IS NULL THEN 1 END) as missing_score,
                   COUNT(CASE WHEN market_temperature IS NULL THEN 1 END) as missing_temperature,
                   COUNT(CASE WHEN rent_value IS NULL THEN 1 END) as missing_rent
            FROM rents.marts.mart_rent_trends
            """
            
            result = conn.execute(query).fetchone()
            total_records = result[0]
            missing_yoy = result[1]
            missing_score = result[2]
            missing_temp = result[3]
            missing_rent = result[4]
            
            # Calculate missing percentages
            missing_yoy_pct = (missing_yoy / total_records * 100) if total_records > 0 else 0
            missing_score_pct = (missing_score / total_records * 100) if total_records > 0 else 0
            missing_temp_pct = (missing_temp / total_records * 100) if total_records > 0 else 0
            missing_rent_pct = (missing_rent / total_records * 100) if total_records > 0 else 0
            
            metadata = {
                "total_records": MetadataValue.int(total_records),
                "missing_yoy_percentage": MetadataValue.float(missing_yoy_pct),
                "missing_score_percentage": MetadataValue.float(missing_score_pct),
                "missing_temperature_percentage": MetadataValue.float(missing_temp_pct),
                "missing_rent_percentage": MetadataValue.float(missing_rent_pct),
            }
            
            # Check if any key metric has > 5% missing values
            max_missing_pct = max(missing_yoy_pct, missing_score_pct, missing_temp_pct, missing_rent_pct)
            
            if max_missing_pct <= 5.0:
                return AssetCheckResult(
                    passed=True,
                    description=f"Data completeness acceptable (max {max_missing_pct:.2f}% missing)",
                    metadata=metadata,
                )
            else:
                severity = AssetCheckSeverity.WARN if max_missing_pct <= 10.0 else AssetCheckSeverity.ERROR
                return AssetCheckResult(
                    passed=False,
                    description=f"High missing data rate (max {max_missing_pct:.2f}% missing)",
                    metadata=metadata,
                    severity=severity,
                )
                
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to check data completeness: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["marts", "mart_market_rankings"],
    description="Check that market heat scores are within expected range (0-100)",
)
def market_heat_score_check(
    context: AssetExecutionContext,
    snowflake: SnowflakeResource
) -> AssetCheckResult:
    """
    Check that market heat scores are within the expected 0-100 range.
    """
    try:
        with snowflake.get_connection() as conn:
            query = """
            SELECT COUNT(*) as total_records,
                   COUNT(CASE WHEN market_heat_score < 0 OR market_heat_score > 100 
                         THEN 1 END) as out_of_range,
                   MIN(market_heat_score) as min_score,
                   MAX(market_heat_score) as max_score,
                   AVG(market_heat_score) as avg_score
            FROM rents.marts.mart_market_rankings
            WHERE market_heat_score IS NOT NULL
            """
            
            result = conn.execute(query).fetchone()
            total_records = result[0]
            out_of_range = result[1]
            min_score = result[2]
            max_score = result[3]
            avg_score = result[4]
            
            out_of_range_pct = (out_of_range / total_records * 100) if total_records > 0 else 0
            
            metadata = {
                "total_records": MetadataValue.int(total_records),
                "out_of_range_records": MetadataValue.int(out_of_range),
                "out_of_range_percentage": MetadataValue.float(out_of_range_pct),
                "min_score": MetadataValue.float(min_score) if min_score else MetadataValue.text("N/A"),
                "max_score": MetadataValue.float(max_score) if max_score else MetadataValue.text("N/A"),
                "avg_score": MetadataValue.float(avg_score) if avg_score else MetadataValue.text("N/A"),
            }
            
            if out_of_range_pct == 0:
                return AssetCheckResult(
                    passed=True,
                    description="All market heat scores within valid range (0-100)",
                    metadata=metadata,
                )
            else:
                return AssetCheckResult(
                    passed=False,
                    description=f"Heat scores out of range: {out_of_range_pct:.2f}% of records",
                    metadata=metadata,
                    severity=AssetCheckSeverity.ERROR,
                )
                
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to check heat scores: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


# Collect all business rule checks
business_rule_checks = [
    zori_growth_bounds_check,
    aptlist_population_check,
    rent_trends_completeness_check,
    market_heat_score_check,
]