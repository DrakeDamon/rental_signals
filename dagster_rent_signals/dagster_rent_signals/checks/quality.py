"""Great Expectations integration as Dagster asset checks."""

import sys
from pathlib import Path
from dagster import (
    asset_check,
    AssetCheckResult,
    AssetExecutionContext,
    AssetCheckSeverity,
    MetadataValue,
)

# Add the great_expectations directory to path for importing validation script
GE_DIR = Path(__file__).parent.parent.parent.parent / "great_expectations"
sys.path.insert(0, str(GE_DIR))

from validate_data_quality import RentSignalsDataValidator


@asset_check(
    asset=["staging", "stg_aptlist"],
    description="Run Great Expectations validation suite for stg_aptlist",
    blocking=True,  # Block downstream assets if this fails
)
def stg_aptlist_quality_check(context: AssetExecutionContext) -> AssetCheckResult:
    """
    Great Expectations validation for ApartmentList staging data.
    
    Validates:
    - Row count within expected range (1K - 500K)
    - Rent index values within reasonable bounds (0-2000)
    - Population data completeness and validity
    - Data quality score distribution
    - Business key uniqueness
    """
    try:
        validator = RentSignalsDataValidator()
        results = validator.validate_staging_models()
        
        stg_aptlist_passed = results.get('stg_aptlist', False)
        
        metadata = {
            "validation_results": MetadataValue.json(results),
            "total_expectations": MetadataValue.int(17),  # Based on existing suite
        }
        
        if stg_aptlist_passed:
            return AssetCheckResult(
                passed=True,
                description="All Great Expectations validations passed",
                metadata=metadata,
            )
        else:
            return AssetCheckResult(
                passed=False,
                description="Some Great Expectations validations failed",
                metadata=metadata,
                severity=AssetCheckSeverity.ERROR,
            )
            
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to run validation: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["staging", "stg_zori"],
    description="Run Great Expectations validation suite for stg_zori",
    blocking=True,
)
def stg_zori_quality_check(context: AssetExecutionContext) -> AssetCheckResult:
    """
    Great Expectations validation for Zillow ZORI staging data.
    
    Validates:
    - Row count within expected range (5K - 1M)
    - ZORI values within reasonable bounds (500-8000)
    - Metro size rank consistency
    - State name format validation
    - Size category enumeration
    """
    try:
        validator = RentSignalsDataValidator()
        results = validator.validate_staging_models()
        
        stg_zori_passed = results.get('stg_zori', False)
        
        metadata = {
            "validation_results": MetadataValue.json(results),
            "total_expectations": MetadataValue.int(15),  # Based on existing suite
        }
        
        if stg_zori_passed:
            return AssetCheckResult(
                passed=True,
                description="All Great Expectations validations passed",
                metadata=metadata,
            )
        else:
            return AssetCheckResult(
                passed=False,
                description="Some Great Expectations validations failed",
                metadata=metadata,
                severity=AssetCheckSeverity.ERROR,
            )
            
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to run validation: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["staging", "stg_fred"],
    description="Run Great Expectations validation suite for stg_fred",
    blocking=True,
)
def stg_fred_quality_check(context: AssetExecutionContext) -> AssetCheckResult:
    """
    Great Expectations validation for FRED economic staging data.
    
    Validates:
    - FRED series ID format validation
    - CPI category enumeration
    - Seasonal adjustment detection
    - Economic indicator value ranges
    - Reliability scoring validation
    """
    try:
        validator = RentSignalsDataValidator()
        results = validator.validate_staging_models()
        
        stg_fred_passed = results.get('stg_fred', False)
        
        metadata = {
            "validation_results": MetadataValue.json(results),
            "total_expectations": MetadataValue.int(12),  # Based on existing suite
        }
        
        if stg_fred_passed:
            return AssetCheckResult(
                passed=True,
                description="All Great Expectations validations passed",
                metadata=metadata,
            )
        else:
            return AssetCheckResult(
                passed=False,
                description="Some Great Expectations validations failed",
                metadata=metadata,
                severity=AssetCheckSeverity.ERROR,
            )
            
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to run validation: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["core", "fact_rent_zori"],
    description="Run Great Expectations validation suite for fact_rent_zori",
    blocking=False,  # Don't block marts for core fact issues
)
def fact_rent_zori_quality_check(context: AssetExecutionContext) -> AssetCheckResult:
    """
    Great Expectations validation for Zillow ZORI fact table.
    
    Validates:
    - Fact table grain uniqueness
    - ZORI value business rules
    - YoY/MoM change validation
    - Growth category enumeration
    - National ranking validation
    """
    try:
        validator = RentSignalsDataValidator()
        results = validator.validate_core_models()
        
        fact_rent_zori_passed = results.get('fact_rent_zori', False)
        
        metadata = {
            "validation_results": MetadataValue.json(results),
            "total_expectations": MetadataValue.int(15),  # Based on existing suite
        }
        
        if fact_rent_zori_passed:
            return AssetCheckResult(
                passed=True,
                description="All Great Expectations validations passed",
                metadata=metadata,
            )
        else:
            return AssetCheckResult(
                passed=False,
                description="Some Great Expectations validations failed",
                metadata=metadata,
                severity=AssetCheckSeverity.WARN,
            )
            
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to run validation: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["core", "fact_rent_aptlist"],
    description="Run Great Expectations validation suite for fact_rent_aptlist",
    blocking=False,
)
def fact_rent_aptlist_quality_check(context: AssetExecutionContext) -> AssetCheckResult:
    """
    Great Expectations validation for ApartmentList fact table.
    
    Validates:
    - Population-based validation rules
    - Rent index business rules
    - Market classification validation
    - Cross-reference validation
    - Calculated metric validation
    """
    try:
        validator = RentSignalsDataValidator()
        results = validator.validate_core_models()
        
        fact_rent_aptlist_passed = results.get('fact_rent_aptlist', False)
        
        metadata = {
            "validation_results": MetadataValue.json(results),
            "total_expectations": MetadataValue.int(13),  # Based on existing suite
        }
        
        if fact_rent_aptlist_passed:
            return AssetCheckResult(
                passed=True,
                description="All Great Expectations validations passed",
                metadata=metadata,
            )
        else:
            return AssetCheckResult(
                passed=False,
                description="Some Great Expectations validations failed",
                metadata=metadata,
                severity=AssetCheckSeverity.WARN,
            )
            
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to run validation: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


@asset_check(
    asset=["marts", "mart_rent_trends"],
    description="Run Great Expectations validation suite for mart_rent_trends",
    blocking=False,
)
def mart_rent_trends_quality_check(context: AssetExecutionContext) -> AssetCheckResult:
    """
    Great Expectations validation for rent trends mart.
    
    Validates:
    - Cross-source data validation
    - Market temperature classification
    - Affordability category validation
    - Investment scoring validation
    - Data freshness checks
    """
    try:
        validator = RentSignalsDataValidator()
        results = validator.validate_mart_models(['mart_rent_trends'])
        
        mart_rent_trends_passed = results.get('mart_rent_trends', False)
        
        metadata = {
            "validation_results": MetadataValue.json(results),
            "total_expectations": MetadataValue.int(12),  # Based on existing suite
        }
        
        if mart_rent_trends_passed:
            return AssetCheckResult(
                passed=True,
                description="All Great Expectations validations passed",
                metadata=metadata,
            )
        else:
            return AssetCheckResult(
                passed=False,
                description="Some Great Expectations validations failed",
                metadata=metadata,
                severity=AssetCheckSeverity.WARN,
            )
            
    except Exception as e:
        return AssetCheckResult(
            passed=False,
            description=f"Failed to run validation: {str(e)}",
            severity=AssetCheckSeverity.ERROR,
        )


# Collect all quality checks
quality_checks = [
    stg_aptlist_quality_check,
    stg_zori_quality_check,
    stg_fred_quality_check,
    fact_rent_zori_quality_check,
    fact_rent_aptlist_quality_check,
    mart_rent_trends_quality_check,
]