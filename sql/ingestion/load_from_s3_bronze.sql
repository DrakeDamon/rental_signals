-- ================================================================
-- Snowflake Script: Load ALL Data Sources from S3 Bronze Layer
-- ================================================================
-- This script loads RAW data from S3 bronze layer into Snowflake
-- for dbt to transform through staging → core → marts.
--
-- Prerequisites:
-- 1. S3 bucket with {source}/bronze/date=YYYY-MM/ structure
-- 2. AWS IAM role configured for Snowflake external stage
-- 3. Snowflake database and schemas created
-- ================================================================

USE DATABASE RENTS;
USE SCHEMA RAW;

-- ================================================================
-- STEP 1: Create Storage Integration (One-Time Setup)
-- ================================================================

CREATE STORAGE INTEGRATION IF NOT EXISTS rent_data_s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<ACCOUNT_ID>:role/SnowflakeS3ExternalStage'
  STORAGE_ALLOWED_LOCATIONS = ('s3://<BUCKET_NAME>/');

-- Get Snowflake IAM details for AWS trust policy
DESC STORAGE INTEGRATION rent_data_s3_integration;
-- Copy STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID
-- Use these values to create the IAM role trust policy in AWS


-- ================================================================
-- STEP 2: Create External Stages for Bronze Layer
-- ================================================================

-- Zillow Bronze Stage (CSV files)
CREATE OR REPLACE STAGE zillow_bronze_stage
  STORAGE_INTEGRATION = rent_data_s3_integration
  URL = 's3://<BUCKET_NAME>/zillow/bronze/'
  FILE_FORMAT = (
    TYPE = CSV
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL', 'null')
    TRIM_SPACE = TRUE
  );

-- ApartmentList Bronze Stage (CSV files)
CREATE OR REPLACE STAGE apartmentlist_bronze_stage
  STORAGE_INTEGRATION = rent_data_s3_integration
  URL = 's3://<BUCKET_NAME>/apartmentlist/bronze/'
  FILE_FORMAT = (
    TYPE = CSV
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL', 'null')
    TRIM_SPACE = TRUE
  );

-- FRED Bronze Stage (JSON files)
CREATE OR REPLACE STAGE fred_bronze_stage
  STORAGE_INTEGRATION = rent_data_s3_integration
  URL = 's3://<BUCKET_NAME>/fred/bronze/'
  FILE_FORMAT = (
    TYPE = JSON
    STRIP_OUTER_ARRAY = FALSE
  );

-- Test stage access
LIST @zillow_bronze_stage;
LIST @apartmentlist_bronze_stage;
LIST @fred_bronze_stage;


-- ================================================================
-- STEP 3: Create RAW Tables (Simple Schemas Matching CSV Structure)
-- ================================================================

-- Zillow ZORI Raw Table
CREATE TABLE IF NOT EXISTS RENTS.RAW.ZORI_METRO_LONG (
  REGIONID INTEGER,
  SIZERANK INTEGER,
  METRO VARCHAR(255),
  REGION_TYPE VARCHAR(50),
  STATE_NAME VARCHAR(100),
  MONTH DATE,
  ZORI DECIMAL(10, 2),
  
  -- Metadata
  LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  S3_FILE_PATH VARCHAR(500)
);

-- ApartmentList Raw Table
CREATE TABLE IF NOT EXISTS RENTS.RAW.APTLIST_LONG (
  LOCATION_FIPS_CODE VARCHAR(20),
  REGIONID VARCHAR(50),
  LOCATION_NAME VARCHAR(255),
  LOCATION_TYPE VARCHAR(50),
  STATE VARCHAR(100),
  COUNTY VARCHAR(100),
  METRO VARCHAR(255),
  MONTH DATE,
  RENT_INDEX DECIMAL(10, 2),
  POPULATION INTEGER,
  
  -- Metadata
  LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  S3_FILE_PATH VARCHAR(500)
);

-- FRED Raw Table
CREATE TABLE IF NOT EXISTS RENTS.RAW.FRED_CPI_LONG (
  SERIES_ID VARCHAR(50),
  LABEL VARCHAR(500),
  MONTH DATE,
  VALUE DECIMAL(18, 4),
  
  -- Metadata
  LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  S3_FILE_PATH VARCHAR(500)
);

-- Add clustering for query performance
ALTER TABLE RENTS.RAW.ZORI_METRO_LONG CLUSTER BY (MONTH, METRO);
ALTER TABLE RENTS.RAW.APTLIST_LONG CLUSTER BY (MONTH, LOCATION_NAME);
ALTER TABLE RENTS.RAW.FRED_CPI_LONG CLUSTER BY (SERIES_ID, MONTH);


-- ================================================================
-- STEP 4: Load Data from S3 Bronze Layer
-- ================================================================

-- Load Zillow ZORI (replace YYYY-MM with actual date)
COPY INTO RENTS.RAW.ZORI_METRO_LONG (
  REGIONID,
  SIZERANK,
  METRO,
  REGION_TYPE,
  STATE_NAME,
  MONTH,
  ZORI,
  S3_FILE_PATH
)
FROM (
  SELECT 
    $1::INTEGER,
    $2::INTEGER,
    $3::VARCHAR,
    $4::VARCHAR,
    $5::VARCHAR,
    $6::DATE,
    $7::DECIMAL(10, 2),
    METADATA$FILENAME
  FROM @zillow_bronze_stage/date=2025-09/
)
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1)
ON_ERROR = CONTINUE
PURGE = FALSE;

-- Load ApartmentList
COPY INTO RENTS.RAW.APTLIST_LONG (
  LOCATION_FIPS_CODE,
  REGIONID,
  LOCATION_NAME,
  LOCATION_TYPE,
  STATE,
  COUNTY,
  METRO,
  MONTH,
  RENT_INDEX,
  POPULATION,
  S3_FILE_PATH
)
FROM (
  SELECT 
    $1::VARCHAR,
    $2::VARCHAR,
    $3::VARCHAR,
    $4::VARCHAR,
    $5::VARCHAR,
    $6::VARCHAR,
    $7::VARCHAR,
    $8::DATE,
    $9::DECIMAL(10, 2),
    $10::INTEGER,
    METADATA$FILENAME
  FROM @apartmentlist_bronze_stage/date=2025-09/
)
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1)
ON_ERROR = CONTINUE
PURGE = FALSE;

-- Load FRED (from JSON)
COPY INTO RENTS.RAW.FRED_CPI_LONG (
  SERIES_ID,
  LABEL,
  MONTH,
  VALUE,
  S3_FILE_PATH
)
FROM (
  SELECT 
    $1:series_id::VARCHAR,
    $1:label::VARCHAR,
    $1:month::DATE,
    $1:value::DECIMAL(18, 4),
    METADATA$FILENAME
  FROM @fred_bronze_stage/date=2024-01/
)
FILE_FORMAT = (TYPE = JSON)
ON_ERROR = CONTINUE
PURGE = FALSE;


-- ================================================================
-- STEP 5: Verify Data Load
-- ================================================================

-- Check Zillow data
SELECT 
  COUNT(*) AS row_count,
  COUNT(DISTINCT METRO) AS metro_count,
  MIN(MONTH) AS earliest_month,
  MAX(MONTH) AS latest_month,
  MAX(LOADED_AT) AS last_loaded
FROM RENTS.RAW.ZORI_METRO_LONG;

-- Check ApartmentList data
SELECT 
  COUNT(*) AS row_count,
  COUNT(DISTINCT LOCATION_NAME) AS location_count,
  MIN(MONTH) AS earliest_month,
  MAX(MONTH) AS latest_month,
  MAX(LOADED_AT) AS last_loaded
FROM RENTS.RAW.APTLIST_LONG;

-- Check FRED data
SELECT 
  COUNT(*) AS row_count,
  COUNT(DISTINCT SERIES_ID) AS series_count,
  MIN(MONTH) AS earliest_month,
  MAX(MONTH) AS latest_month,
  MAX(LOADED_AT) AS last_loaded
FROM RENTS.RAW.FRED_CPI_LONG;


-- ================================================================
-- STEP 6: Automated Tasks (Optional - for ongoing loads)
-- ================================================================

-- Zillow load task (runs daily, loads any new data)
CREATE OR REPLACE TASK RENTS.RAW.TASK_LOAD_ZILLOW
  WAREHOUSE = WH_XS
  SCHEDULE = 'USING CRON 0 6 * * * America/New_York'
AS
  COPY INTO RENTS.RAW.ZORI_METRO_LONG
  FROM (
    SELECT 
      $1::INTEGER, $2::INTEGER, $3::VARCHAR, $4::VARCHAR,
      $5::VARCHAR, $6::DATE, $7::DECIMAL(10, 2),
      METADATA$FILENAME
    FROM @zillow_bronze_stage
  )
  FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1)
  ON_ERROR = CONTINUE
  PURGE = FALSE;

-- ApartmentList load task
CREATE OR REPLACE TASK RENTS.RAW.TASK_LOAD_APARTMENTLIST
  WAREHOUSE = WH_XS
  SCHEDULE = 'USING CRON 0 7 * * * America/New_York'
AS
  COPY INTO RENTS.RAW.APTLIST_LONG
  FROM (
    SELECT 
      $1::VARCHAR, $2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR,
      $6::VARCHAR, $7::VARCHAR, $8::DATE, $9::DECIMAL(10, 2), $10::INTEGER,
      METADATA$FILENAME
    FROM @apartmentlist_bronze_stage
  )
  FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1)
  ON_ERROR = CONTINUE
  PURGE = FALSE;

-- FRED load task
CREATE OR REPLACE TASK RENTS.RAW.TASK_LOAD_FRED
  WAREHOUSE = WH_XS
  SCHEDULE = 'USING CRON 0 8 * * * America/New_York'
AS
  COPY INTO RENTS.RAW.FRED_CPI_LONG
  FROM (
    SELECT 
      $1:series_id::VARCHAR, $1:label::VARCHAR,
      $1:month::DATE, $1:value::DECIMAL(18, 4),
      METADATA$FILENAME
    FROM @fred_bronze_stage
  )
  FILE_FORMAT = (TYPE = JSON)
  ON_ERROR = CONTINUE
  PURGE = FALSE;

-- Enable tasks (uncomment when ready)
-- ALTER TASK RENTS.RAW.TASK_LOAD_ZILLOW RESUME;
-- ALTER TASK RENTS.RAW.TASK_LOAD_APARTMENTLIST RESUME;
-- ALTER TASK RENTS.RAW.TASK_LOAD_FRED RESUME;


-- ================================================================
-- STEP 7: Grant Permissions for dbt
-- ================================================================

-- Grant access to dbt role
GRANT USAGE ON DATABASE RENTS TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA RENTS.RAW TO ROLE DBT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA RENTS.RAW TO ROLE DBT_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA RENTS.RAW TO ROLE DBT_ROLE;

-- Grant access to dbt target schemas
GRANT USAGE ON SCHEMA RENTS.ANALYTICS TO ROLE DBT_ROLE;
GRANT ALL ON SCHEMA RENTS.ANALYTICS TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA RENTS.MARTS TO ROLE DBT_ROLE;
GRANT ALL ON SCHEMA RENTS.MARTS TO ROLE DBT_ROLE;


-- ================================================================
-- STEP 8: Data Quality Checks
-- ================================================================

-- Check for duplicates in Zillow
SELECT 
  METRO,
  MONTH,
  COUNT(*) AS record_count
FROM RENTS.RAW.ZORI_METRO_LONG
GROUP BY METRO, MONTH
HAVING COUNT(*) > 1;

-- Check for duplicates in ApartmentList
SELECT 
  LOCATION_NAME,
  MONTH,
  COUNT(*) AS record_count
FROM RENTS.RAW.APTLIST_LONG
GROUP BY LOCATION_NAME, MONTH
HAVING COUNT(*) > 1;

-- Check for duplicates in FRED
SELECT 
  SERIES_ID,
  MONTH,
  COUNT(*) AS record_count
FROM RENTS.RAW.FRED_CPI_LONG
GROUP BY SERIES_ID, MONTH
HAVING COUNT(*) > 1;


-- ================================================================
-- STEP 9: Next Steps - dbt Transformation
-- ================================================================

/*
After loading RAW data, run dbt to transform through the layers:

1. dbt Staging (Clean & Standardize):
   dbt run --models staging
   Creates: RENTS.ANALYTICS.STG_ZORI
           RENTS.ANALYTICS.STG_APTLIST
           RENTS.ANALYTICS.STG_FRED

2. dbt Core (Star Schema + SCD Type 2):
   dbt run --models core
   Creates: RENTS.ANALYTICS.DIM_LOCATION
           RENTS.ANALYTICS.DIM_TIME
           RENTS.ANALYTICS.FACT_RENT_ZORI
           RENTS.ANALYTICS.FACT_RENT_APTLIST
           RENTS.ANALYTICS.FACT_ECONOMIC_INDICATOR

3. dbt Marts (Business Views):
   dbt run --models marts
   Creates: RENTS.MARTS.VW_RENT_TRENDS
           RENTS.MARTS.VW_MARKET_RANKINGS
           RENTS.MARTS.VW_ECONOMIC_CORRELATION
           RENTS.MARTS.VW_REGIONAL_SUMMARY
           RENTS.MARTS.VW_DATA_LINEAGE

4. Run Tests:
   dbt test
   python great_expectations/validate_data_quality.py --layer all

5. Generate Documentation:
   dbt docs generate && dbt docs serve
*/


-- ================================================================
-- Monitoring Queries
-- ================================================================

-- Overall data freshness
SELECT 
  'Zillow' AS source,
  MAX(MONTH) AS latest_month,
  MAX(LOADED_AT) AS last_load,
  COUNT(*) AS total_rows
FROM RENTS.RAW.ZORI_METRO_LONG
UNION ALL
SELECT 
  'ApartmentList',
  MAX(MONTH),
  MAX(LOADED_AT),
  COUNT(*)
FROM RENTS.RAW.APTLIST_LONG
UNION ALL
SELECT 
  'FRED',
  MAX(MONTH),
  MAX(LOADED_AT),
  COUNT(*)
FROM RENTS.RAW.FRED_CPI_LONG
ORDER BY source;

-- S3 file tracking
SELECT 
  'Zillow' AS source,
  S3_FILE_PATH,
  COUNT(*) AS records,
  MIN(MONTH) AS min_month,
  MAX(MONTH) AS max_month
FROM RENTS.RAW.ZORI_METRO_LONG
GROUP BY S3_FILE_PATH
ORDER BY MAX(LOADED_AT) DESC;


