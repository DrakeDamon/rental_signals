-- Snowflake Setup SQL Commands
-- Run these commands in your Snowflake console

-- 1. Create storage integration
CREATE OR REPLACE STORAGE INTEGRATION rent_signals_s3_integration
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'S3'
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::607709788146:role/SnowflakeS3ExternalStage'
    STORAGE_ALLOWED_LOCATIONS = ('s3://rent-signals-dev-dd/');

-- 2. Verify the storage integration
DESC STORAGE INTEGRATION rent_signals_s3_integration;

-- 2b. Create named file formats for better debugging
CREATE OR REPLACE FILE FORMAT FF_CSV_HEADER_QUOTED
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_DELIMITER = ','
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL', 'null')
    EMPTY_FIELD_AS_NULL = TRUE;

-- 3. Create external stage for ApartmentList data
CREATE OR REPLACE STAGE apt_list_stage
    STORAGE_INTEGRATION = rent_signals_s3_integration
    URL = 's3://rent-signals-dev-dd/aptlist/'
    FILE_FORMAT = FF_CSV_HEADER_QUOTED;

-- 4. Create external stage for Zillow data (long format)
CREATE OR REPLACE STAGE zillow_stage
    STORAGE_INTEGRATION = rent_signals_s3_integration
    URL = 's3://rent-signals-dev-dd/zillow/metro/'
    FILE_FORMAT = FF_CSV_HEADER_QUOTED;

-- 4b. Alternative stage names for clarity
CREATE OR REPLACE STAGE S3_ZORI_METRO_STAGE
    STORAGE_INTEGRATION = rent_signals_s3_integration
    URL = 's3://rent-signals-dev-dd/zillow/metro/'
    FILE_FORMAT = FF_CSV_HEADER_QUOTED;

-- 5. Create external stage for FRED data
CREATE OR REPLACE STAGE fred_stage
    STORAGE_INTEGRATION = rent_signals_s3_integration
    URL = 's3://rent-signals-dev-dd/fred/'
    FILE_FORMAT = FF_CSV_HEADER_QUOTED;

-- 6. Create tables for long format data
CREATE OR REPLACE TABLE apt_list_raw (
    location_name STRING,
    location_type STRING,
    location_fips_code STRING,
    population STRING,
    state STRING,
    county STRING,
    metro STRING,
    rent_index FLOAT,
    month DATE
);

CREATE OR REPLACE TABLE zori_metro_long (
    regionid NUMBER,
    sizerank NUMBER,
    metro STRING,
    region_type STRING,
    state_name STRING,
    month DATE,
    zori FLOAT
);

-- 7. Load ApartmentList data from external stage
COPY INTO apt_list_raw
FROM @apt_list_stage
PATTERN = '.*\.csv'
ON_ERROR = 'CONTINUE';

-- 8. Load Zillow Metro data (long format)
COPY INTO zori_metro_long (regionid, sizerank, metro, region_type, state_name, month, zori)
FROM (
  SELECT 
    TRY_TO_NUMBER($1),
    TRY_TO_NUMBER($2),
    $3::STRING,
    $4::STRING,
    $5::STRING,
    TO_DATE($6),
    TRY_TO_NUMBER($7)
  FROM @zillow_stage
  WHERE $1 RLIKE '^[0-9]+$'  -- Skip header rows
)
ON_ERROR = 'CONTINUE';

-- 9. Verify data loaded successfully
SELECT COUNT(*) as apt_list_rows FROM apt_list_raw;
SELECT COUNT(*) as zori_metro_rows FROM zori_metro_long;
SELECT * FROM apt_list_raw LIMIT 5;
SELECT * FROM zori_metro_long ORDER BY month DESC LIMIT 5;

-- 10. Create stored procedure for automated data loading
CREATE OR REPLACE PROCEDURE load_rent_signals_data()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Clear existing data
    TRUNCATE TABLE apt_list_raw;
    TRUNCATE TABLE zori_metro_long;
    
    -- Load ApartmentList data
    COPY INTO apt_list_raw
    FROM @apt_list_stage
    PATTERN = '.*\.csv'
    ON_ERROR = 'CONTINUE';
    
    -- Load Zillow Metro data (long format)
    COPY INTO zori_metro_long (regionid, sizerank, metro, region_type, state_name, month, zori)
    FROM (
      SELECT 
        TRY_TO_NUMBER($1),
        TRY_TO_NUMBER($2),
        $3::STRING,
        $4::STRING,
        $5::STRING,
        TO_DATE($6),
        TRY_TO_NUMBER($7)
      FROM @zillow_stage
      WHERE $1 RLIKE '^[0-9]+$'  -- Skip header rows
    )
    ON_ERROR = 'CONTINUE';
    
    RETURN 'Data loading completed successfully for both ApartmentList and Zillow data';
END;
$$;

-- 11. Execute the stored procedure
CALL load_rent_signals_data();