# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern Tampa rental signals data pipeline that collects, standardizes, and analyzes rental market data from multiple sources (Zillow, ApartmentList, FRED). The system uses **dbt Core** for analytics engineering, **Great Expectations** for data quality validation, and **Snowflake** as the cloud data warehouse. The pipeline implements a **Bronze → Silver → Gold** architecture with SCD Type 2 historical tracking.

## Required Environment Variables

### AWS Infrastructure

Before running any AWS infrastructure commands, export these variables:

```bash
export AWS_PROFILE=default
export AWS_REGION=us-east-1
export BUCKET=rent-signals-dev-<initials-or-random>   # must be globally unique
export TODAY=$(date +%F)
```

### Snowflake Connection (for dbt and Great Expectations)

```bash
export SNOWFLAKE_ACCOUNT="<YOUR_SNOWFLAKE_ACCOUNT>"
export SNOWFLAKE_USER="<YOUR_SNOWFLAKE_USER>"
export SNOWFLAKE_PASSWORD="<YOUR_SNOWFLAKE_PASSWORD>"
export SNOWFLAKE_DATABASE="<YOUR_DATABASE_NAME>"      # e.g., RENTS
export SNOWFLAKE_WAREHOUSE="<YOUR_WAREHOUSE_NAME>"    # e.g., WH_XS
export SNOWFLAKE_ROLE="<YOUR_ROLE_NAME>"              # e.g., ACCOUNTADMIN
export SNOWFLAKE_SCHEMA="<YOUR_DBT_SCHEMA>"           # e.g., DBT_DEV
```

## Common Commands

### Modern Dagster Orchestration (Recommended)

- `cd dagster_rent_signals && pip install -e ".[dev]"` - Install Dagster project
- `dagster dev` - Start local Dagster UI (http://localhost:3000)

#### Data Ingestion (New!)

- `dagster asset materialize zillow_zori_ingestion` - Run Zillow ZORI ingestion (downloads, transforms, uploads to S3)
- Navigate to Assets → ingestion group in Dagster UI for visual materialization
- Automated monthly schedule runs on 2nd of each month at 3 AM EST

#### dbt Pipeline Execution

- `dagster job execute staging_pipeline` - Run staging pipeline
- `dagster job execute core_pipeline` - Run core pipeline (after staging)
- `dagster job execute marts_pipeline` - Run marts pipeline (after core)
- `dagster job execute full_refresh_pipeline` - Run complete end-to-end pipeline
- `dagster asset materialize stg_aptlist stg_zori stg_fred` - Run specific assets

### Direct dbt + Great Expectations (Legacy)

- `cd dbt_rent_signals && dbt deps` - Install dbt dependencies
- `dbt run --models staging` - Run staging models (data cleaning)
- `dbt run --models core` - Run core models (star schema)
- `dbt run --models marts` - Run mart models (business analytics)
- `dbt test` - Run dbt data quality tests
- `dbt docs generate && dbt docs serve` - Generate and serve documentation

### Data Quality Validation (Direct)

- `cd great_expectations` - Navigate to Great Expectations directory
- `python validate_data_quality.py --layer all` - Run all validation suites
- `python validate_data_quality.py --layer staging` - Validate staging models only
- `python validate_data_quality.py --layer core` - Validate core models only
- `python validate_data_quality.py --fail-fast` - Exit on first validation failure

### Legacy Data Processing (Still Available)

- `python scripts/standardize.py` - Transform raw data files from wide to long format
- Processes three data sources:
  - ApartmentList: `data/raw/aptlist/` → `standardized/apartmentlist_long.csv`
  - Zillow ZORI: `data/raw/zillow/` → `standardized/zori_zip_long.csv`
  - FRED: `data/raw/fred/` → `standardized/fred_cpi_long.csv`

### AWS Infrastructure Setup

- `make help` - Show all available targets and required environment variables
- `make create-bucket create-prefixes upload-samples verify` - Complete S3 setup
- `make create-readonly-policy` - Create IAM policy for Snowflake (prints ARN for later use)
- `make verify` - Verify S3 bucket configuration and uploaded files

### Individual AWS Tasks

- `make create-bucket` - Create secure S3 bucket (handles us-east-1 special case)
- `make create-prefixes` - Create date-based prefixes (zillow/, aptlist/, fred/)
- `make upload-samples` - Upload standardized CSVs to S3
- `make create-oidc-role` - Create GitHub OIDC role for CI/CD uploads

## Architecture

### Modern Data Stack (Bronze → Silver → Gold)

1. **🥉 Bronze Layer**: Raw data ingested from S3 to Snowflake tables
2. **🥈 Silver Layer**: dbt staging and core models with SCD Type 2 historical tracking
3. **🥇 Gold Layer**: dbt mart models optimized for business analytics
4. **🔍 Quality Layer**: Great Expectations validation at each stage
5. **⚙️ Orchestration**: Dagster software-defined assets with scheduling and monitoring

### Data Flow (Modern Pipeline)

1. **Raw Data**: CSV files uploaded to S3 in `{source}/YYYY-MM-DD/` format
2. **Bronze Ingestion**: Snowflake external tables or COPY commands load raw data
3. **Silver Processing**: dbt staging models clean and standardize data
4. **Core Models**: dbt builds star schema with SCD Type 2 snapshots
5. **Gold Analytics**: dbt mart models provide business-ready views
6. **Quality Gates**: Great Expectations validates data at each layer

### Data Sources

- **Zillow ZORI**: Metro area rent index data (wide → long format via dbt)
- **ApartmentList**: County/metro rent estimates with population data
- **FRED Economic**: CPI and economic indicators (already long format)

### Technology Stack

- **Analytics Engineering**: dbt Core for transformation and modeling
- **Data Quality**: Great Expectations with 100+ validation rules
- **Data Warehouse**: Snowflake with optimized clustering and partitioning
- **Orchestration**: Dagster with software-defined assets, scheduling, and monitoring
- **Version Control**: Git-based workflow for all models, expectations, and assets
- **Documentation**: Auto-generated lineage via dbt docs, Great Expectations, and Dagster UI

### AWS Infrastructure

- **S3 Bucket**: Private, encrypted, versioned storage with blocked public access
- **IAM Policies**: Least-privilege access scoped to specific S3 prefixes
- **Snowflake Integration**: External stage role for data warehouse access
- **GitHub OIDC**: Keyless CI/CD authentication for automated uploads

### Security Model

- No AWS credentials in repository
- Environment variable based configuration
- Template files with placeholders for sensitive values
- OIDC authentication for GitHub Actions
- Least-privilege IAM policies scoped to required S3 prefixes only

## Data Schema

### Standardized Output Format

All standardized files follow long format with consistent date column:

- **month**: DateTime column (YYYY-MM-DD format)
- **Source-specific columns**: Geographic identifiers and metrics
- **No null/missing month values**: Filtered during standardization

### Key File Locations

- **Raw data**: `data/raw/{source}/YYYY-MM-DD/`
- **Standardized data**: `standardized/{source}_long.csv`
- **dbt project**: `dbt_rent_signals/` (models, snapshots, macros, tests)
- **Great Expectations**: `great_expectations/` (expectations, checkpoints, validation)
- **Dagster orchestration**: `dagster_rent_signals/` (assets, jobs, schedules, sensors)
- **AWS policies**: `infra/aws/policies/`
- **Setup documentation**: `infra/aws/README.md`

## Modern Dagster Orchestration Workflow

### Daily Pipeline Execution (Automated)

1. **Data Freshness Sensor**: Monitors Snowflake raw tables for new data
2. **Staging Pipeline**: Triggered automatically or daily at 6 AM EST
   - Materializes staging assets (stg_aptlist, stg_zori, stg_fred)
   - Runs data quality checks and freshness validation
   - Blocks downstream if critical issues found
3. **Core Pipeline**: Triggered after staging completion
   - Builds snapshots for SCD Type 2 tracking
   - Materializes dimension and fact tables
   - Validates business rules and data integrity
4. **Marts Pipeline**: Triggered after core completion
   - Creates business-ready analytics models
   - Validates completeness and business metrics
   - Updates operational monitoring dashboards
5. **Weekly Full Refresh**: Complete pipeline refresh on Sundays at 2 AM EST

### Development Workflow

1. **Asset Development**: Create/modify dbt models and corresponding Dagster assets
2. **Add Checks**: Create asset checks for validation and business rules
3. **Local Testing**: `dagster dev` and test individual assets or pipelines
4. **Quality Validation**: Asset checks run automatically during materialization
5. **Documentation**: Update asset descriptions and business context
6. **Version Control**: Commit dbt models, Dagster assets, and validation logic

### Direct dbt + Great Expectations Workflow (Legacy)

### Daily Pipeline Execution

1. **Data Ingestion**: Load new data from S3 to Snowflake raw tables
2. **dbt Staging**: `dbt run --models staging` - Clean and standardize data
3. **Quality Check**: `python validate_data_quality.py --layer staging`
4. **dbt Core**: `dbt run --models core` - Build star schema with SCD Type 2
5. **Quality Check**: `python validate_data_quality.py --layer core`
6. **dbt Marts**: `dbt run --models marts` - Create business analytics views
7. **Quality Check**: `python validate_data_quality.py --layer marts`
8. **Documentation**: `dbt docs generate` - Update lineage and documentation

### Development Workflow

1. **Model Development**: Create/modify dbt models in `dbt_rent_signals/models/`
2. **Add Tests**: Create Great Expectations suites in `great_expectations/expectations/`
3. **Local Testing**: `dbt run --models my_model` and validation
4. **Documentation**: Update model descriptions and add business context
5. **Version Control**: Commit both dbt models and expectation suites

## Snowflake Integration Workflow

1. Create S3 infrastructure and upload data using Makefile
2. Create IAM policy with `make create-readonly-policy` (copy the ARN)
3. Create Snowflake storage integration pointing to the S3 bucket
4. Get Snowflake IAM details with `DESC STORAGE INTEGRATION`
5. Fill trust template with Snowflake-provided ARN and External ID
6. Create IAM role for Snowflake and attach the policy

## Development Notes

### Adding New Data Sources (Modern Dagster Stack)

1. **Raw Data Setup**: Add new source to S3 structure and IAM policies
2. **dbt Staging**: Create staging model in `dbt_rent_signals/models/staging/`
3. **Dagster Asset**: Create corresponding asset in `dagster_rent_signals/assets/staging.py`
4. **Asset Checks**: Add quality and freshness checks in `dagster_rent_signals/checks/`
5. **Core Integration**: Add to dimensions/facts and create corresponding assets
6. **Business Analytics**: Create mart models and assets in `dagster_rent_signals/assets/marts.py`
7. **Pipeline Jobs**: Update job definitions to include new assets
8. **Documentation**: Update asset descriptions and business context
9. **Testing**: Validate full pipeline execution with `dagster dev`

### Adding New Data Sources (Legacy)

- Add processing logic to `scripts/standardize.py`
- Add corresponding S3 prefix to Makefile targets
- Update IAM policies to include new prefix
- Ensure consistent long format output with month column

### Dagster Best Practices

- **Software-Defined Assets**: Each dbt model should have a corresponding asset
- **Asset Checks**: Comprehensive validation for each asset (quality, freshness, business rules)
- **Metadata Tracking**: Capture row counts, execution time, and validation results
- **Dependencies**: Use AssetIn to define clear asset dependencies
- **Job Organization**: Group related assets into logical pipelines
- **Scheduling**: Use sensors for event-driven execution, schedules for regular refresh

### dbt Best Practices

- **Staging**: Clean and standardize, add data quality scores
- **Core**: Use SCD Type 2 snapshots for slowly changing dimensions
- **Marts**: Business-ready models with pre-calculated metrics
- **Tests**: Generic and singular tests for data quality
- **Documentation**: Rich descriptions with business context

### Great Expectations Best Practices

- **Layer-specific validation**: Different standards for staging vs marts
- **Business rule focus**: Validate what matters to stakeholders
- **Performance**: Use sampling for large datasets when needed
- **Version control**: All expectation suites tracked in Git

### RESTful API Commands

- `cd rent_signals_api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` - Start API locally
- Visit `http://localhost:8000/docs` - Interactive API documentation (Swagger UI)
- Visit `http://localhost:8000/redoc` - Alternative API documentation (ReDoc)
- `curl http://localhost:8000/v1/health` - Health check endpoint
- `curl http://localhost:8000/v1/markets?limit=5` - Test market data endpoint
- `curl http://localhost:8000/v1/prices/drops?threshold=10` - Test price drops endpoint

### API Deployment (Render)

- **Repository**: Connected to GitHub repo (auto-deploy on push)
- **Root Directory**: `rent_signals_api` (set in Render dashboard)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: Snowflake credentials, API config, logging settings
- **Health Check**: `/v1/health` endpoint for monitoring

### API Endpoints Summary

- **GET /v1/markets** - List rental markets with summary stats
- **GET /v1/markets/{metro}/trends** - Historical trends for specific metro
- **GET /v1/markets/compare** - Compare multiple markets side-by-side
- **GET /v1/prices/drops** - Markets with recent price drops
- **GET /v1/rankings/top** - Top market rankings by category
- **GET /v1/economics/correlation** - Rent vs inflation analysis
- **GET /v1/regional/summary** - State and regional aggregations
- **GET /v1/data/lineage** - Data quality and lineage monitoring
- **GET /v1/health** - System health check

### When modifying AWS infrastructure:

- All policies use `${BUCKET}` placeholder for environment variable substitution
- Makefile handles us-east-1 bucket creation special case
- Templates (.TEMPLATE files) require manual placeholder replacement

### API Development Best Practices

- **Error Handling**: Comprehensive HTTP status codes with structured JSON responses
- **Input Validation**: Pydantic models with query parameter validation
- **URL Normalization**: Metro slug standardization for consistent routing
- **Pagination**: Limit/offset parameters with configurable maximum limits
- **Logging**: Structured JSON logging with request/response metadata
- **Documentation**: Auto-generated OpenAPI spec with comprehensive examples
- **Health Monitoring**: Database connectivity checks and system status reporting
