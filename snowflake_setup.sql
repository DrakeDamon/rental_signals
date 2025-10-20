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

-- 3. Create external stage for ApartmentList data
CREATE OR REPLACE STAGE apt_list_stage
    STORAGE_INTEGRATION = rent_signals_s3_integration
    URL = 's3://rent-signals-dev-dd/aptlist/'
    FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);

-- 4. Create external stage for Zillow data  
CREATE OR REPLACE STAGE zillow_stage
    STORAGE_INTEGRATION = rent_signals_s3_integration
    URL = 's3://rent-signals-dev-dd/zillow/'
    FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);

-- 5. Create external stage for FRED data
CREATE OR REPLACE STAGE fred_stage
    STORAGE_INTEGRATION = rent_signals_s3_integration
    URL = 's3://rent-signals-dev-dd/fred/'
    FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);

-- 6. Test data loading (ApartmentList example)
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

-- 7. Load data from external stage
COPY INTO apt_list_raw
FROM @apt_list_stage
PATTERN = '.*\.csv'
ON_ERROR = 'CONTINUE';

-- 8. Verify data loaded successfully
SELECT COUNT(*) as total_rows FROM apt_list_raw;
SELECT * FROM apt_list_raw LIMIT 10;

-- 9. Create stored procedure for automated data loading
CREATE OR REPLACE PROCEDURE load_rent_signals_data()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Clear existing data
    TRUNCATE TABLE apt_list_raw;
    
    -- Load fresh data
    COPY INTO apt_list_raw
    FROM @apt_list_stage
    PATTERN = '.*\.csv'
    ON_ERROR = 'CONTINUE';
    
    RETURN 'Data loading completed successfully';
END;
$$;

-- 10. Execute the stored procedure
CALL load_rent_signals_data();