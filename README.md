# Tampa Rent Signals Data Pipeline

A comprehensive data engineering pipeline for collecting, processing, and analyzing rental market data from multiple sources. The system integrates data from Zillow, ApartmentList, and Federal Reserve Economic Data (FRED) into a production-ready Snowflake data warehouse.

## 🏗️ Architecture Overview

### Data Flow Architecture
The system implements a **Bronze → Silver → Gold** layered architecture with SCD Type 2 historical tracking:

```mermaid
flowchart TD
    subgraph Sources["🌐 Data Sources"]
        A1[📊 ApartmentList<br/>Rent Estimates]
        A2[🏠 Zillow ZORI<br/>Metro Rent Index]
        A3[🏛️ FRED CPI<br/>Economic Indicators]
    end

    subgraph Bronze["🥉 Bronze Layer (RAW)"]
        B1[APTLIST_LONG<br/>Raw CSV Data]
        B2[ZORI_METRO_LONG<br/>Raw CSV Data]
        B3[FRED_CPI_LONG<br/>Raw CSV Data]
    end

    subgraph Silver["🥈 Silver Layer (ANALYTICS)"]
        C1[DIM_LOCATION<br/>SCD Type 2]
        C2[DIM_TIME<br/>Calendar]
        C3[DIM_ECONOMIC_SERIES<br/>SCD Type 2]
        C4[DIM_DATA_SOURCE<br/>Static]
        D1[FACT_RENT_ZORI<br/>Rent Facts]
        D2[FACT_RENT_APTLIST<br/>Rent Facts]
        D3[FACT_ECONOMIC_INDICATOR<br/>CPI Facts]
    end

    subgraph Gold["🥇 Gold Layer (BUSINESS VIEWS)"]
        E1[VW_RENT_TRENDS<br/>📈 Growth Analysis]
        E2[VW_MARKET_RANKINGS<br/>🏆 Heat Scores]
        E3[VW_ECONOMIC_CORRELATION<br/>💰 Rent vs CPI]
        E4[VW_REGIONAL_SUMMARY<br/>🗺️ State Aggregates]
        E5[VW_DATA_LINEAGE<br/>🔍 Quality Monitor]
    end

    subgraph ETL["⚙️ ETL Processes"]
        F1[SP_LOAD_DIM_LOCATION_SCD2<br/>📍 Geographic Updates]
        F2[SP_LOAD_FACT_RENT_ZORI<br/>🏠 Zillow Processing]
        F3[SP_LOAD_FACT_RENT_APTLIST<br/>🏢 ApartmentList Processing]
        F4[SP_FULL_ETL_PROCESS<br/>🔄 Master Orchestration]
    end

    %% Data Flow
    A1 --> B1
    A2 --> B2
    A3 --> B3

    B1 --> F1
    B2 --> F1
    B1 --> F3
    B2 --> F2
    B3 --> ETL

    F1 --> C1
    ETL --> C2
    ETL --> C3
    ETL --> C4
    F2 --> D1
    F3 --> D2
    ETL --> D3

    C1 --> E1
    C2 --> E1
    D1 --> E1
    D2 --> E1

    C1 --> E2
    D1 --> E2
    D2 --> E2

    D1 --> E3
    D2 --> E3
    D3 --> E3

    C1 --> E4
    D1 --> E4
    D2 --> E4

    C1 --> E5
    C3 --> E5
    C4 --> E5

    %% Styling
    classDef sourceStyle fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef bronzeStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef silverStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef goldStyle fill:#fff8e1,stroke:#ff6f00,stroke-width:2px
    classDef etlStyle fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px

    class A1,A2,A3 sourceStyle
    class B1,B2,B3 bronzeStyle
    class C1,C2,C3,C4,D1,D2,D3 silverStyle
    class E1,E2,E3,E4,E5 goldStyle
    class F1,F2,F3,F4 etlStyle
```

### Processing Layers
1. **🥉 Bronze (RAW)**: Raw CSV files ingested from S3 with minimal processing
2. **🥈 Silver (ANALYTICS)**: Cleaned, validated star schema with SCD Type 2 historical tracking  
3. **🥇 Gold (BUSINESS)**: Aggregated, business-friendly views optimized for analytics
4. **⚙️ ETL**: Automated stored procedures handling all data transformations

## 📁 Project Structure

```
├── data/                    # Raw data files (local development)
│   └── raw/
│       ├── aptlist/        # ApartmentList data
│       ├── fred/           # Federal Reserve economic data
│       └── zillow/         # Zillow ZORI data
├── docs/                   # Documentation and sample data
│   └── diagrams/          # Mermaid architecture diagrams
├── infra/                  # Infrastructure as code
│   └── aws/               # AWS infrastructure components
│       ├── policies/      # IAM policies and trust relationships
│       └── README.md      # AWS setup instructions
├── scripts/               # Data processing and utility scripts
│   ├── standardize.py     # Main data transformation script
│   ├── debug_csv_locally.sh    # Local CSV validation
│   ├── test_pipeline_end_to_end.sh  # End-to-end testing
│   └── *.py              # Source-specific processing scripts
├── sql/                   # Data warehouse SQL components
│   ├── schema/           # Database schema definitions
│   ├── etl/              # ETL stored procedures
│   ├── views/            # Analytics and business intelligence views
│   ├── debug/            # Debugging and troubleshooting scripts
│   └── README.md         # SQL components documentation
├── standardized/         # Processed data in standardized format
├── temp/                 # Temporary files and debug outputs
├── CLAUDE.md            # AI assistant guidance
├── Makefile             # Infrastructure automation commands
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.8+ with pandas
- Snowflake account with necessary privileges
- Make utility for infrastructure automation

### 1. Environment Setup

```bash
# Set required environment variables
export AWS_PROFILE=default
export AWS_REGION=us-east-1
export BUCKET=rent-signals-dev-<your-initials>
export TODAY=$(date +%F)
```

### 2. Infrastructure Deployment

```bash
# View all available commands
make help

# Deploy complete infrastructure
make create-bucket create-prefixes upload-samples verify

# Create IAM policies for Snowflake integration
make create-readonly-policy
```

### 3. Data Processing

```bash
# Transform raw data to standardized format
python scripts/standardize.py

# Validate processed data locally
./scripts/debug_csv_locally.sh

# Run end-to-end pipeline test
./scripts/test_pipeline_end_to_end.sh
```

### 4. Data Warehouse Setup

```sql
-- 1. Run initial setup
@sql/schema/snowflake_setup.sql

-- 2. Create star schema
@sql/schema/analytics_schema_ddl.sql

-- 3. Deploy ETL procedures
@sql/etl/etl_procedures.sql

-- 4. Create analytics views
@sql/views/gold_layer_views.sql

-- 5. Run full ETL process
CALL RENTS.ANALYTICS.SP_FULL_ETL_PROCESS();
```

## 🏛️ Data Warehouse Design

### Star Schema with SCD Type 2

The data warehouse implements a dimensional model optimized for analytical queries with full historical tracking:

```mermaid
erDiagram
    DIM_LOCATION ||--o{ FACT_RENT_ZORI : has
    DIM_LOCATION ||--o{ FACT_RENT_APTLIST : has
    DIM_TIME ||--o{ FACT_RENT_ZORI : has
    DIM_TIME ||--o{ FACT_RENT_APTLIST : has
    DIM_TIME ||--o{ FACT_ECONOMIC_INDICATOR : has
    DIM_ECONOMIC_SERIES ||--o{ FACT_ECONOMIC_INDICATOR : describes
    DIM_DATA_SOURCE ||--o{ FACT_RENT_ZORI : provides
    DIM_DATA_SOURCE ||--o{ FACT_RENT_APTLIST : provides
    DIM_DATA_SOURCE ||--o{ FACT_ECONOMIC_INDICATOR : provides

    DIM_LOCATION {
        INT LOCATION_KEY PK
        VARCHAR LOCATION_FIPS_CODE
        INT REGION_ID
        VARCHAR LOCATION_NAME
        VARCHAR LOCATION_TYPE
        VARCHAR STATE_NAME
        INT POPULATION
        DATE EFFECTIVE_DATE
        DATE END_DATE
        BOOLEAN IS_CURRENT
    }

    DIM_TIME {
        INT TIME_KEY PK
        DATE MONTH_DATE
        INT YEAR
        INT QUARTER
        INT MONTH_NUMBER
        VARCHAR MONTH_NAME
        BOOLEAN IS_CURRENT_MONTH
    }

    DIM_ECONOMIC_SERIES {
        INT SERIES_KEY PK
        VARCHAR SERIES_ID
        VARCHAR SERIES_LABEL
        VARCHAR CATEGORY
        VARCHAR FREQUENCY
        DATE EFFECTIVE_DATE
        DATE END_DATE
        BOOLEAN IS_CURRENT
    }

    DIM_DATA_SOURCE {
        INT SOURCE_KEY PK
        VARCHAR SOURCE_NAME
        VARCHAR SOURCE_SYSTEM
        VARCHAR DATA_TYPE
        INT RELIABILITY_SCORE
    }

    FACT_RENT_ZORI {
        INT TIME_KEY FK
        INT LOCATION_KEY FK
        INT SOURCE_KEY FK
        INT REGIONID
        DATE MONTH_DATE
        DECIMAL ZORI_VALUE
        INT SIZE_RANK
        DECIMAL YOY_CHANGE
        DECIMAL YOY_PCT_CHANGE
        DECIMAL MOM_CHANGE
        DECIMAL MOM_PCT_CHANGE
        INT DATA_QUALITY_SCORE
        BOOLEAN HAS_ANOMALY
    }

    FACT_RENT_APTLIST {
        INT TIME_KEY FK
        INT LOCATION_KEY FK
        INT SOURCE_KEY FK
        VARCHAR LOCATION_FIPS_CODE
        DATE MONTH_DATE
        DECIMAL RENT_INDEX
        INT POPULATION
        DECIMAL YOY_CHANGE
        DECIMAL YOY_PCT_CHANGE
        DECIMAL MOM_CHANGE
        DECIMAL MOM_PCT_CHANGE
        INT DATA_QUALITY_SCORE
        BOOLEAN HAS_ANOMALY
    }

    FACT_ECONOMIC_INDICATOR {
        INT TIME_KEY FK
        INT SERIES_KEY FK
        INT SOURCE_KEY FK
        VARCHAR SERIES_ID
        DATE MONTH_DATE
        DECIMAL INDICATOR_VALUE
        DECIMAL YOY_CHANGE
        DECIMAL YOY_PCT_CHANGE
        DECIMAL MOM_CHANGE
        DECIMAL MOM_PCT_CHANGE
        INT DATA_QUALITY_SCORE
        BOOLEAN IS_REVISED
    }
```

**Key Features:**
- **🔄 SCD Type 2**: Historical tracking for dimensions that change over time (LOCATION, ECONOMIC_SERIES)
- **📊 Pre-calculated Measures**: YoY/MoM changes computed during ETL for performance
- **🛡️ Data Quality**: Built-in scoring (1-10) and statistical anomaly detection
- **⚡ Performance**: Clustered fact tables and materialized views for fast queries
- **📋 Lineage**: Complete data provenance tracking from source to analytics

### Analytics Layer

Business-friendly views for common analytical patterns:
- **VW_RENT_TRENDS**: Comprehensive rent trend analysis
- **VW_MARKET_RANKINGS**: Metro competitiveness and heat scores
- **VW_ECONOMIC_CORRELATION**: Rent vs inflation correlation
- **VW_REGIONAL_SUMMARY**: State and national aggregations
- **VW_DATA_LINEAGE**: Data quality monitoring

## 📊 Data Sources

### Zillow ZORI (Zillow Observed Rent Index)
- **Coverage**: Metro areas across the United States
- **Frequency**: Monthly updates
- **Metrics**: Rent index values, year-over-year changes
- **Format**: Wide format (monthly columns) → standardized to long format

### ApartmentList
- **Coverage**: Counties and metro areas
- **Frequency**: Monthly updates
- **Metrics**: Rent estimates, population data
- **Format**: Wide format (YYYY_MM columns) → standardized to long format

### Federal Reserve Economic Data (FRED)
- **Coverage**: National economic indicators
- **Frequency**: Monthly updates
- **Metrics**: Consumer Price Index (CPI), Housing CPI
- **Format**: Already in long format

## 🔧 ETL Process

### Data Standardization
All data sources are transformed to a consistent long format:
```
month | location_id | metric_value | [source-specific columns]
```

### Loading Strategy
1. **Extract**: Download from source APIs/files
2. **Transform**: Standardize format and validate quality
3. **Load**: Upload to S3 with date partitioning
4. **Warehouse**: ETL procedures with SCD Type 2 logic

### Data Quality Measures
- **Validation**: Schema validation and data type checks
- **Anomaly Detection**: Statistical outlier identification
- **Completeness**: Null value and missing data tracking
- **Consistency**: Cross-source data validation

## 🔐 Security & Compliance

### AWS Security
- **S3 Buckets**: Private with encryption at rest
- **IAM Policies**: Least-privilege access controls
- **OIDC Integration**: Keyless GitHub Actions authentication
- **No Credentials**: Environment variable based configuration

### Data Governance
- **Lineage Tracking**: Complete data provenance
- **Version Control**: All code and configurations in Git
- **Documentation**: Comprehensive inline and external docs
- **Audit Trail**: Snowflake query history and load logs

## 🚨 Troubleshooting

### Common Issues

**CSV Loading Errors:**
```sql
@sql/debug/debug_snowflake_csv.sql
```

**Data Quality Issues:**
```sql
SELECT * FROM RENTS.GOLD.VW_DATA_LINEAGE;
```

**Local Validation:**
```bash
./scripts/debug_csv_locally.sh
```

### Debug Tools
- Local CSV inspection scripts
- Snowflake validation queries
- End-to-end pipeline testing
- Data lineage and quality monitoring views

## 📈 Usage Examples

### Business Analytics

```sql
-- Top 10 fastest growing rental markets
SELECT 
    LOCATION_NAME,
    STATE_NAME,
    YOY_PCT_CHANGE,
    RENT_VALUE
FROM RENTS.GOLD.VW_RENT_TRENDS 
WHERE DATA_SOURCE = 'Zillow ZORI'
ORDER BY YOY_PCT_CHANGE DESC
LIMIT 10;

-- Rent vs inflation correlation
SELECT 
    YEAR,
    QUARTER,
    AVG(RENT_CPI_SPREAD) AS rent_inflation_spread
FROM RENTS.GOLD.VW_ECONOMIC_CORRELATION
WHERE YEAR >= 2020
GROUP BY YEAR, QUARTER
ORDER BY YEAR, QUARTER;
```

### Operational Monitoring

```sql
-- Data freshness dashboard
SELECT 
    SOURCE_NAME,
    DAYS_SINCE_LATEST_DATA,
    DATA_QUALITY_STATUS,
    RECORD_COUNT
FROM RENTS.GOLD.VW_DATA_LINEAGE;
```

## 🛠️ Development

### Adding New Data Sources
1. Create extraction script in `scripts/`
2. Add transformation logic to `standardize.py`
3. Update S3 structure and IAM policies
4. Create corresponding fact/dimension tables
5. Add ETL procedures and analytics views

### Testing
- Unit tests for transformation scripts
- Integration tests for ETL procedures
- End-to-end pipeline validation
- Data quality monitoring

## 📄 License

This project is for educational and analytical purposes. Data sources have their own terms of use.

## 🤝 Contributing

This is a demonstration project. For production use, consider:
- Additional data validation
- Enhanced error handling
- Monitoring and alerting
- Performance optimization
- Security hardening