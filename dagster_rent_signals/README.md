# Dagster Orchestration for Tampa Rent Signals

Modern orchestration layer for the Tampa Rent Signals data pipeline using Dagster's software-defined assets approach.

## 🎯 Overview

This Dagster project orchestrates a comprehensive data pipeline that:

- Transforms raw rent data using **dbt Core** models
- Validates data quality with **Great Expectations** integration
- Manages **SCD Type 2** historical tracking with snapshots
- Provides comprehensive **observability** and monitoring
- Automates scheduling and sensor-based triggering

## 🏗️ Architecture

### Software-Defined Assets

**Staging Layer (3 assets):**

- `stg_aptlist` - ApartmentList data with quality scoring
- `stg_zori` - Zillow ZORI data with metro categorization
- `stg_fred` - FRED economic data with series validation

**Core Layer (7 assets):**

- `dim_time` - Calendar dimension
- `dim_data_source` - Data source reference
- `snap_location` / `dim_location` - Location SCD Type 2
- `snap_economic_series` / `dim_economic_series` - Economic series SCD Type 2
- `fact_rent_zori` - Zillow rent facts
- `fact_rent_aptlist` - ApartmentList rent facts
- `fact_economic_indicator` - Economic indicator facts

**Mart Layer (5 assets):**

- `mart_rent_trends` - Cross-source rent analysis
- `mart_market_rankings` - Metro competitiveness rankings
- `mart_economic_correlation` - Rent vs inflation analysis
- `mart_regional_summary` - State/national aggregates
- `mart_data_lineage` - Operational monitoring

### Asset Checks

**Data Quality Checks (6):**

- Great Expectations integration for all staging, core, and mart models
- 100+ validation rules from existing GE suites
- Blocking vs. non-blocking severity levels

**Freshness Checks (4):**

- Staging data < 24 hours old
- Mart data < 72 hours old
- Automated staleness detection

**Business Rule Checks (4):**

- YoY rent growth within bounds (-50% to +100%)
- Population values positive and reasonable
- Data completeness for key metrics
- Market heat scores within range (0-100)

## 🚀 Quick Start

### 1. Installation

```bash
cd dagster_rent_signals
pip install -e ".[dev]"
```

### 2. Environment Setup

Set required environment variables (use placeholders):

```bash
# Snowflake connection
export SNOWFLAKE_ACCOUNT="<YOUR_SNOWFLAKE_ACCOUNT>"
export SNOWFLAKE_USER="<YOUR_SNOWFLAKE_USER>"
export SNOWFLAKE_PASSWORD="<YOUR_SNOWFLAKE_PASSWORD>"
export SNOWFLAKE_DATABASE="<YOUR_DATABASE_NAME>"      # e.g., RENTS
export SNOWFLAKE_WAREHOUSE="<YOUR_WAREHOUSE_NAME>"    # e.g., WH_XS
export SNOWFLAKE_ROLE="<YOUR_ROLE_NAME>"              # e.g., ACCOUNTADMIN
export SNOWFLAKE_SCHEMA="<YOUR_DBT_SCHEMA>"           # e.g., DBT_DEV
```

### 3. Start Dagster UI

```bash
# For local development
dagster dev

# For production deployment
dagster-webserver -h 0.0.0.0 -p 3000 -w workspace.yaml
```

### 4. Run Pipelines

**Via Dagster UI:**

- Navigate to http://localhost:3000
- Go to "Jobs" and select a pipeline
- Click "Launch Run"

**Via CLI:**

```bash
# Run staging pipeline
dagster job execute staging_pipeline

# Run full refresh
dagster job execute full_refresh_pipeline

# Run specific assets
dagster asset materialize stg_aptlist stg_zori stg_fred
```

## 📋 Pipeline Jobs

### `staging_pipeline`

- **Purpose**: Process raw data into staging models
- **Assets**: All staging assets
- **Schedule**: Daily at 6 AM EST
- **Checks**: Data quality and freshness validation

### `core_pipeline`

- **Purpose**: Build star schema from staging data
- **Assets**: Dimensions, facts, and snapshots
- **Dependencies**: Requires staging completion
- **Checks**: Business rule validation

### `marts_pipeline`

- **Purpose**: Create business-ready analytics
- **Assets**: All mart models
- **Dependencies**: Requires core completion
- **Checks**: Completeness and business metrics

### `full_refresh_pipeline`

- **Purpose**: Complete end-to-end refresh
- **Assets**: All assets (staging → core → marts)
- **Schedule**: Weekly on Sundays at 2 AM EST
- **Checks**: Comprehensive validation suite

## ⏰ Scheduling & Automation

### Schedules

- **Daily Refresh**: Staging pipeline at 6 AM EST daily
- **Weekly Validation**: Full pipeline on Sundays at 2 AM EST

### Sensors

- **Data Freshness Sensor**: Monitors Snowflake raw tables for new data
- **Trigger Logic**: Launches staging pipeline when fresh data detected
- **Cooldown**: 1-hour minimum between sensor-triggered runs

## 🔍 Monitoring & Observability

### Dagster UI Features

- **Asset Lineage**: Visual dependency graph
- **Run History**: Success/failure tracking with detailed logs
- **Asset Checks**: Real-time validation status
- **Metadata Tracking**: Row counts, execution times, validation results

### Key Metrics Tracked

- **Asset Execution**: Duration, success rate, failure reasons
- **Data Quality**: Validation pass/fail rates, specific expectation failures
- **Data Freshness**: Time since last update per source
- **Business Metrics**: YoY growth, market heat scores, completeness rates

## 🧪 Development Workflow

### Local Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Start local Dagster UI
dagster dev

# Format code
black .
isort .

# Type checking
mypy dagster_rent_signals/
```

### Adding New Assets

1. Create new dbt model in `../dbt_rent_signals/models/`
2. Add corresponding asset in appropriate `assets/` module
3. Add asset checks in `checks/` modules
4. Update job definitions if needed
5. Add tests and documentation

### Testing Strategy

- **Unit Tests**: Asset function logic
- **Integration Tests**: Full pipeline execution
- **Asset Check Tests**: Validation logic
- **Performance Tests**: Large dataset handling

## 🚀 Deployment

### Production Deployment

```bash
# Build container
docker build -t rent-signals-dagster .

# Deploy to production
# (Kubernetes, ECS, or other container orchestration)

# Configure production resources
# - Snowflake connection pooling
# - Enhanced logging and monitoring
# - Alerting integration
```

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
- name: Run Dagster Tests
  run: |
    cd dagster_rent_signals
    dagster job execute full_refresh_pipeline --preset test
```

## 📊 Business Value

### Operational Benefits

- **Automated Orchestration**: No manual pipeline execution
- **Proactive Monitoring**: Asset checks catch issues before downstream impact
- **Complete Observability**: Full lineage and execution tracking
- **Flexible Scheduling**: Daily, weekly, and event-driven execution

### Technical Benefits

- **Software-Defined Infrastructure**: All pipeline logic in version control
- **Incremental Processing**: Smart re-computation based on dependencies
- **Failure Recovery**: Built-in retry logic and error handling
- **Development Velocity**: Easy testing and iteration of pipeline changes

### Data Quality Benefits

- **Continuous Validation**: 100+ automated data quality checks
- **Early Detection**: Issues caught at staging before propagating
- **Business Rule Enforcement**: Automated validation of key metrics
- **Comprehensive Reporting**: Detailed validation results and trends

## 🔧 Configuration

### Environment Variables

- `SNOWFLAKE_*`: Database connection parameters
- `DBT_PROFILES_DIR`: dbt profiles directory (optional)
- `DAGSTER_HOME`: Dagster instance home (optional)

### Resource Configuration

Resources can be configured per environment:

- **Development**: Local dbt execution, reduced validation
- **Staging**: Full validation, limited scheduling
- **Production**: All features enabled, enhanced monitoring

## 📚 Documentation

- **Asset Documentation**: Auto-generated from dbt model descriptions
- **Lineage Diagrams**: Visual representation in Dagster UI
- **Check Documentation**: Detailed validation rule explanations
- **Operational Runbooks**: Available in Dagster UI metadata

## 🤝 Support

For issues or questions:

1. Check Dagster UI for run logs and asset check results
2. Review validation reports in Great Expectations data docs
3. Examine dbt documentation for model-specific details
4. Consult this README and inline code documentation
