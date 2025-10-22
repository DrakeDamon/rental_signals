-- ============================================================================
-- Full Snowflake CSV Debug Script
-- Validates GitHub → S3 → Snowflake pipeline for zori_metro CSV issues
-- ============================================================================

-- Set context
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE WH_XS;
USE DATABASE RENTS;
USE SCHEMA RAW;

-- ============================================================================
-- STEP 1: Validate Current Snowflake Setup
-- ============================================================================

SHOW FILE FORMATS LIKE '%CSV%';

-- Check if we have named file formats
DESC FILE FORMAT FF_CSV_HDR;

-- Inspect current stages
SHOW STAGES LIKE '%ZORI%' OR LIKE '%ZILLOW%';

-- Detailed stage inspection
DESC STAGE S3_ZORI_METRO_STAGE;

-- ============================================================================
-- STEP 2: Test File Accessibility and Structure
-- ============================================================================

-- List files in the S3 path to confirm they exist
LIST @S3_ZORI_METRO_STAGE/2025-10-20/;

-- Alternative paths to check
LIST @S3_ZORI_METRO_STAGE/2025-10-21/;

-- ============================================================================
-- STEP 3: Test CSV Reading with Different Approaches
-- ============================================================================

-- Test 1: Try reading with current stage configuration
SELECT *
FROM @S3_ZORI_METRO_STAGE/2025-10-20/zori_metro_wide.csv
LIMIT 5;

-- Test 2: If above fails, try reading as single column blob
SELECT $1
FROM @S3_ZORI_METRO_STAGE/2025-10-20/zori_metro_wide.csv
LIMIT 3;

-- Test 3: Try with explicit file format
SELECT $1, $2, $3, $4, $5, $6, $7, $8
FROM @S3_ZORI_METRO_STAGE/2025-10-20/zori_metro_wide.csv
(FILE_FORMAT => (TYPE=CSV, SKIP_HEADER=1, FIELD_OPTIONALLY_ENCLOSED_BY='"'))
LIMIT 3;

-- Test 4: Try reading the long format file instead
SELECT *
FROM @S3_ZORI_METRO_STAGE/2025-10-20/zori_metro_long.csv
LIMIT 5;

-- Test 5: Try long format with explicit column selection
SELECT $1, $2, $3, $4, $5, $6, $7
FROM @S3_ZORI_METRO_STAGE/2025-10-20/zori_metro_long.csv
(FILE_FORMAT => (TYPE=CSV, SKIP_HEADER=1, FIELD_OPTIONALLY_ENCLOSED_BY='"'))
LIMIT 5;

-- ============================================================================
-- STEP 4: Create Proper Named File Format
-- ============================================================================

-- Create a properly configured CSV file format
CREATE OR REPLACE FILE FORMAT FF_CSV_HEADER_QUOTED
TYPE = CSV
SKIP_HEADER = 1
FIELD_DELIMITER = ','
FIELD_OPTIONALLY_ENCLOSED_BY = '"'
NULL_IF = ('', 'NULL', 'null')
EMPTY_FIELD_AS_NULL = TRUE;

-- Test with the new file format
SELECT $1, $2, $3, $4, $5, $6, $7
FROM @S3_ZORI_METRO_STAGE/2025-10-20/zori_metro_long.csv
(FILE_FORMAT => FF_CSV_HEADER_QUOTED)
LIMIT 5;

-- ============================================================================
-- STEP 5: Create Corrected Stage for Long Format Data
-- ============================================================================

-- Create stage specifically for long format Zillow data
CREATE OR REPLACE STAGE S3_ZORI_METRO_LONG_STAGE
STORAGE_INTEGRATION = rent_signals_s3_integration
URL = 's3://rent-signals-dev-dd/zillow/metro/'
FILE_FORMAT = FF_CSV_HEADER_QUOTED;

-- Test the new stage
SELECT *
FROM @S3_ZORI_METRO_LONG_STAGE/2025-10-20/zori_metro_long.csv
LIMIT 5;

-- ============================================================================
-- STEP 6: Validate Schema Alignment
-- ============================================================================

-- Check if table exists and compare with CSV structure
SHOW TABLES LIKE 'ZORI_METRO_LONG';

-- If table exists, show its structure
DESC TABLE ZORI_METRO_LONG;

-- Test COPY INTO with explicit column mapping
COPY INTO ZORI_METRO_LONG (REGIONID, SIZERANK, METRO, REGION_TYPE, STATE_NAME, MONTH, ZORI)
FROM (
  SELECT 
    TRY_TO_NUMBER($1) as REGIONID,
    TRY_TO_NUMBER($2) as SIZERANK,
    $3::STRING as METRO,
    $4::STRING as REGION_TYPE,
    $5::STRING as STATE_NAME,
    TRY_TO_DATE($6) as MONTH,
    TRY_TO_NUMBER($7) as ZORI
  FROM @S3_ZORI_METRO_LONG_STAGE/2025-10-20/zori_metro_long.csv
  WHERE $1 RLIKE '^[0-9]+$'  -- Skip header rows
)
ON_ERROR = 'CONTINUE'
VALIDATION_MODE = 'RETURN_ERRORS';

-- ============================================================================
-- STEP 7: Diagnostic Queries
-- ============================================================================

-- Count rows in table after attempted load
SELECT COUNT(*) as total_rows FROM ZORI_METRO_LONG;

-- Show sample data with data types
SELECT 
  REGIONID,
  SIZERANK,
  METRO,
  REGION_TYPE,
  STATE_NAME,
  MONTH,
  ZORI,
  TYPEOF(REGIONID) as regionid_type,
  TYPEOF(MONTH) as month_type,
  TYPEOF(ZORI) as zori_type
FROM ZORI_METRO_LONG 
ORDER BY MONTH DESC 
LIMIT 10;

-- Check for data quality issues
SELECT 
  COUNT(*) as total_rows,
  COUNT(REGIONID) as valid_regionid,
  COUNT(MONTH) as valid_month,
  COUNT(ZORI) as valid_zori,
  MIN(MONTH) as earliest_date,
  MAX(MONTH) as latest_date
FROM ZORI_METRO_LONG;

-- ============================================================================
-- STEP 8: Error Analysis
-- ============================================================================

-- Check COPY command history for errors
SELECT 
  QUERY_TEXT,
  EXECUTION_STATUS,
  ERROR_MESSAGE,
  START_TIME
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE QUERY_TEXT ILIKE '%COPY INTO ZORI_METRO_LONG%'
ORDER BY START_TIME DESC
LIMIT 5;

-- Show any load errors in detail
SELECT *
FROM TABLE(VALIDATE(@S3_ZORI_METRO_LONG_STAGE/2025-10-20/zori_metro_long.csv, FILE_FORMAT=>'FF_CSV_HEADER_QUOTED'))
LIMIT 10;