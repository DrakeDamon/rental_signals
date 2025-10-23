"""Mart layer assets for Tampa Rent Signals pipeline."""

from dagster import (
    asset,
    AssetExecutionContext,
    AssetIn,
    FreshnessPolicy,
    MetadataValue,
    Output,
)
from dagster_dbt import DbtCliResource


@asset(
    key=["marts", "mart_rent_trends"],
    ins={
        "fact_rent_zori": AssetIn(["core", "fact_rent_zori"]),
        "fact_rent_aptlist": AssetIn(["core", "fact_rent_aptlist"]),
        "dim_location": AssetIn(["core", "dim_location"]),
        "dim_time": AssetIn(["core", "dim_time"]),
    },
    description="Cross-source rent trend analysis with investment attractiveness scoring",
    group_name="marts_analytics",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 72),  # 72 hours
    metadata={
        "layer": "marts",
        "type": "analytics",
        "dbt_model": "mart_rent_trends",
        "business_purpose": "investment_analysis",
    },
)
def mart_rent_trends(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Comprehensive rent trend analysis combining all data sources.
    
    Features:
    - Cross-source rent trend reconciliation
    - Market temperature classification (Hot, Warm, Cool)
    - Investment attractiveness scoring (1-100)
    - Affordability category analysis
    - YoY/MoM growth categorization
    - Risk assessment and recommendations
    """
    dbt_build_result = dbt.cli(["run", "--select", "mart_rent_trends"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "mart_rent_trends"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["marts", "mart_market_rankings"],
    ins={
        "fact_rent_zori": AssetIn(["core", "fact_rent_zori"]),
        "fact_rent_aptlist": AssetIn(["core", "fact_rent_aptlist"]),
        "dim_location": AssetIn(["core", "dim_location"]),
    },
    description="Metro area competitiveness rankings with heat scores and investment recommendations",
    group_name="marts_analytics",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 72),  # 72 hours
    metadata={
        "layer": "marts",
        "type": "analytics",
        "dbt_model": "mart_market_rankings",
        "business_purpose": "market_comparison",
    },
)
def mart_market_rankings(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Market competitiveness rankings and heat score analysis.
    
    Features:
    - Metro area heat scores (0-100 scale)
    - Market size category rankings
    - Growth momentum analysis
    - Investment recommendation engine
    - Risk-adjusted return projections
    - Competitive positioning analysis
    """
    dbt_build_result = dbt.cli(["run", "--select", "mart_market_rankings"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "mart_market_rankings"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["marts", "mart_economic_correlation"],
    ins={
        "fact_rent_zori": AssetIn(["core", "fact_rent_zori"]),
        "fact_rent_aptlist": AssetIn(["core", "fact_rent_aptlist"]),
        "fact_economic_indicator": AssetIn(["core", "fact_economic_indicator"]),
        "dim_time": AssetIn(["core", "dim_time"]),
    },
    description="Rent vs inflation correlation analysis with policy implications",
    group_name="marts_analytics",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 72),  # 72 hours
    metadata={
        "layer": "marts",
        "type": "analytics",
        "dbt_model": "mart_economic_correlation",
        "business_purpose": "policy_analysis",
    },
)
def mart_economic_correlation(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Economic correlation analysis between rent and inflation indicators.
    
    Features:
    - Rent vs CPI correlation analysis
    - Economic regime classification
    - Affordability pressure indicators
    - Policy implication analysis
    - Leading/lagging indicator identification
    - Regional economic impact assessment
    """
    dbt_build_result = dbt.cli(["run", "--select", "mart_economic_correlation"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "mart_economic_correlation"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["marts", "mart_regional_summary"],
    ins={
        "fact_rent_zori": AssetIn(["core", "fact_rent_zori"]),
        "fact_rent_aptlist": AssetIn(["core", "fact_rent_aptlist"]),
        "dim_location": AssetIn(["core", "dim_location"]),
    },
    description="State and national market characterization with regional insights",
    group_name="marts_summaries",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 72),  # 72 hours
    metadata={
        "layer": "marts",
        "type": "summary",
        "dbt_model": "mart_regional_summary",
        "business_purpose": "executive_reporting",
    },
)
def mart_regional_summary(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Regional market characterization and state-level aggregations.
    
    Features:
    - State-level market summaries
    - National benchmark comparisons
    - Regional growth patterns
    - Market concentration analysis
    - Economic diversity indicators
    - Policy impact assessments
    """
    dbt_build_result = dbt.cli(["run", "--select", "mart_regional_summary"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "mart_regional_summary"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


@asset(
    key=["marts", "mart_data_lineage"],
    ins={
        "dim_location": AssetIn(["core", "dim_location"]),
        "dim_economic_series": AssetIn(["core", "dim_economic_series"]),
        "dim_data_source": AssetIn(["core", "dim_data_source"]),
    },
    description="Operational data quality monitoring and source tracking",
    group_name="marts_summaries", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 72),  # 72 hours
    metadata={
        "layer": "marts",
        "type": "operational",
        "dbt_model": "mart_data_lineage",
        "business_purpose": "data_governance",
    },
)
def mart_data_lineage(context: AssetExecutionContext, dbt: DbtCliResource) -> Output[None]:
    """
    Operational data quality and lineage monitoring dashboard.
    
    Features:
    - Data freshness tracking by source
    - Quality score trending
    - Source reliability monitoring
    - Pipeline health indicators
    - SLA compliance tracking
    - Anomaly detection summary
    """
    dbt_build_result = dbt.cli(["run", "--select", "mart_data_lineage"], context=context)
    
    # Extract metadata from dbt run results
    run_results = dbt_build_result.get_dbt_result()
    model_result = next((r for r in run_results.results if r.node.name == "mart_data_lineage"), None)
    
    metadata = {}
    if model_result and hasattr(model_result, 'adapter_response'):
        metadata.update({
            "rows_affected": MetadataValue.int(getattr(model_result.adapter_response, 'rows_affected', 0)),
            "execution_time_seconds": MetadataValue.float(model_result.execution_time),
            "materialization": MetadataValue.text("table"),
        })
    
    return Output(None, metadata=metadata)


# Collect all mart assets
mart_assets = [
    mart_rent_trends,
    mart_market_rankings,
    mart_economic_correlation,
    mart_regional_summary,
    mart_data_lineage,
]