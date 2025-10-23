"""
Dagster orchestration for Tampa Rent Signals data pipeline.

This package provides software-defined assets for a modern data stack including:
- dbt models as Dagster assets
- Great Expectations validation as asset checks
- Snowflake integration for data warehousing
- Comprehensive observability and monitoring
"""

from .definitions import defs

__all__ = ["defs"]