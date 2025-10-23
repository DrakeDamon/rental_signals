# SQL Components - Tampa Rent Signals Data Warehouse

This directory contains all SQL components for the Tampa rent signals data warehouse implementation in Snowflake.

## Directory Structure

```
sql/
├── schema/          # Data warehouse schema definitions
├── etl/            # Extract, Transform, Load procedures
├── views/          # Business intelligence and analytics views
├── debug/          # Debug and troubleshooting scripts
└── README.md       # This file
```

## Schema Design Overview

The data warehouse implements a **star schema** with **SCD Type 2** (Slowly Changing Dimensions) for historical tracking of dimension changes.

### Visual Architecture
For a comprehensive view of the data warehouse design, see the architecture diagrams:
- **Star Schema ERD**: `../docs/diagrams/star-schema.mmd` - Entity relationship diagram showing all table relationships
- **Data Flow**: `../docs/diagrams/data-flow.mmd` - Bronze → Silver → Gold processing layers
- **Complete Documentation**: `../README.md` - Full project overview with embedded diagrams

### Core Components

1. **Dimension Tables**
   - `DIM_TIME` (SCD Type 0 - Static)
   - `DIM_LOCATION` (SCD Type 2 - Historical tracking)
   - `DIM_ECONOMIC_SERIES` (SCD Type 2 - Historical tracking)
   - `DIM_DATA_SOURCE` (SCD Type 1 - Overwrite changes)

2. **Fact Tables**
   - `FACT_RENT_ZORI` (Zillow rent index facts)
   - `FACT_RENT_APTLIST` (ApartmentList rent facts)
   - `FACT_ECONOMIC_INDICATOR` (Economic indicator facts)

3. **Analytics Views**
   - Business-friendly views for reporting and analysis
   - Pre-calculated measures and rankings
   - Data quality monitoring views

## File Descriptions

### Schema Files (`schema/`)

- **`analytics_schema_ddl.sql`**: Complete star schema definition with all dimension and fact tables
- **`snowflake_setup.sql`**: Initial Snowflake database and schema setup

### ETL Files (`etl/`)

- **`etl_procedures.sql`**: Comprehensive ETL stored procedures including:
  - SCD Type 2 dimension loading procedures
  - Fact table loading with calculated measures
  - Master orchestration procedure (`SP_FULL_ETL_PROCESS`)

### Views Files (`views/`)

- **`gold_layer_views.sql`**: Business intelligence views including:
  - `VW_RENT_TRENDS`: Comprehensive rent trend analysis
  - `VW_MARKET_RANKINGS`: Metro competitiveness rankings
  - `VW_ECONOMIC_CORRELATION`: Rent vs CPI correlation analysis
  - `VW_REGIONAL_SUMMARY`: State and national aggregations
  - `VW_DATA_LINEAGE`: Data quality monitoring

### Debug Files (`debug/`)

- **`debug_snowflake_csv.sql`**: Comprehensive debugging script for CSV loading issues

## Usage Instructions

### 1. Initial Setup

```sql
-- Run in order:
-- 1. Database setup
@sql/schema/snowflake_setup.sql

-- 2. Create schema
@sql/schema/analytics_schema_ddl.sql

-- 3. Create ETL procedures
@sql/etl/etl_procedures.sql

-- 4. Create analytics views
@sql/views/gold_layer_views.sql
```

### 2. ETL Operations

```sql
-- Full ETL process (loads all dimensions and facts)
CALL RENTS.ANALYTICS.SP_FULL_ETL_PROCESS();

-- ETL for specific date range
CALL RENTS.ANALYTICS.SP_FULL_ETL_PROCESS('2024-01-01', '2024-12-31');
```

### 3. Data Analysis

```sql
-- Top 10 fastest growing metros
SELECT 
    LOCATION_NAME,
    STATE_NAME,
    RENT_VALUE,
    YOY_PCT_CHANGE,
    GROWTH_CATEGORY
FROM RENTS.GOLD.VW_RENT_TRENDS 
WHERE DATA_SOURCE = 'Zillow ZORI'
AND YEAR = YEAR(CURRENT_DATE())
ORDER BY YOY_PCT_CHANGE DESC
LIMIT 10;

-- Market heat scores
SELECT 
    STATE_NAME,
    MARKET_HEAT_SCORE,
    MARKET_CLASSIFICATION
FROM RENTS.GOLD.VW_MARKET_RANKINGS
ORDER BY MARKET_HEAT_SCORE DESC;

-- Data quality monitoring
SELECT 
    SOURCE_NAME,
    DATA_FRESHNESS_STATUS,
    DATA_QUALITY_STATUS,
    DAYS_SINCE_LATEST_DATA
FROM RENTS.GOLD.VW_DATA_LINEAGE;
```

## SCD Type 2 Implementation

### Key Features

1. **Historical Tracking**: Maintains complete history of dimension changes
2. **Time-Aware Joins**: Ensures facts are joined to correct dimension versions
3. **Hash-Based Change Detection**: Efficient identification of changed records
4. **Automated ETL**: Stored procedures handle all SCD Type 2 logic

### Example Time-Aware Join

```sql
-- Join facts to historical dimension data (as of fact date)
SELECT f.*, d.LOCATION_NAME, d.POPULATION
FROM RENTS.ANALYTICS.FACT_RENT_ZORI f
JOIN RENTS.ANALYTICS.DIM_LOCATION d 
  ON f.LOCATION_KEY = d.LOCATION_KEY 
 AND f.MONTH_DATE BETWEEN d.EFFECTIVE_DATE AND COALESCE(d.END_DATE, CURRENT_DATE());
```

## Data Quality Features

1. **Anomaly Detection**: Statistical outlier identification
2. **Data Quality Scoring**: 1-10 scale for data completeness and validity
3. **Lineage Tracking**: Source file and load timestamp tracking
4. **Validation Rules**: Constraints and check conditions

## Performance Optimizations

1. **Clustered Tables**: Fact tables clustered by time and location keys
2. **Materialized Views**: Pre-aggregated summaries for fast querying
3. **Proper Indexing**: SCD Type 2 aware indexes on dimension tables
4. **Efficient ETL**: Bulk operations with hash-based change detection

## Troubleshooting

If you encounter issues:

1. Run the debug script: `@sql/debug/debug_snowflake_csv.sql`
2. Check data lineage: `SELECT * FROM RENTS.GOLD.VW_DATA_LINEAGE;`
3. Validate ETL results: `CALL SP_FULL_ETL_PROCESS();`

## Dependencies

- Snowflake database with appropriate permissions
- S3 storage integration configured
- Raw data tables in `RENTS.RAW` schema
- Properly formatted CSV files in S3