-- ============================================================================
-- ETL STORED PROCEDURES FOR RENT SIGNALS DATA WAREHOUSE
-- Handles SCD Type 2 for dimensions and fact table loading
-- ============================================================================

USE SCHEMA RENTS.ANALYTICS;

-- ============================================================================
-- UTILITY PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SP_GENERATE_TIME_DIMENSION: Populate the time dimension
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_GENERATE_TIME_DIMENSION(
    START_YEAR INT DEFAULT 2015,
    END_YEAR INT DEFAULT 2030
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    result_msg STRING;
BEGIN
    -- Clear existing data
    TRUNCATE TABLE DIM_TIME;
    
    -- Generate monthly records
    INSERT INTO DIM_TIME (
        TIME_KEY,
        MONTH_DATE,
        YEAR,
        QUARTER,
        MONTH_NUMBER,
        MONTH_NAME,
        QUARTER_NAME,
        FISCAL_YEAR,
        IS_CURRENT_MONTH,
        MONTHS_AGO
    )
    WITH date_sequence AS (
        SELECT 
            DATE_FROM_PARTS(year_num, month_num, 1) AS month_date,
            year_num,
            month_num
        FROM (
            SELECT ROW_NUMBER() OVER (ORDER BY NULL) + START_YEAR - 1 AS year_num
            FROM TABLE(GENERATOR(ROWCOUNT => (END_YEAR - START_YEAR + 1)))
        ) years
        CROSS JOIN (
            SELECT ROW_NUMBER() OVER (ORDER BY NULL) AS month_num
            FROM TABLE(GENERATOR(ROWCOUNT => 12))
        ) months
    )
    SELECT
        YEAR(month_date) * 100 + MONTH(month_date) AS TIME_KEY,
        month_date AS MONTH_DATE,
        YEAR(month_date) AS YEAR,
        QUARTER(month_date) AS QUARTER,
        MONTH(month_date) AS MONTH_NUMBER,
        MONTHNAME(month_date) AS MONTH_NAME,
        'Q' || QUARTER(month_date) || ' ' || YEAR(month_date) AS QUARTER_NAME,
        CASE 
            WHEN MONTH(month_date) >= 10 THEN YEAR(month_date) + 1
            ELSE YEAR(month_date)
        END AS FISCAL_YEAR,
        month_date = DATE_TRUNC('MONTH', CURRENT_DATE()) AS IS_CURRENT_MONTH,
        DATEDIFF('MONTH', month_date, DATE_TRUNC('MONTH', CURRENT_DATE())) AS MONTHS_AGO
    FROM date_sequence
    ORDER BY month_date;
    
    result_msg := 'Generated ' || (SELECT COUNT(*) FROM DIM_TIME) || ' time dimension records';
    RETURN result_msg;
END;
$$;

-- ----------------------------------------------------------------------------
-- SP_LOAD_DIM_DATA_SOURCE: Load static source system data
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_DATA_SOURCE()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Insert static source data
    MERGE INTO DIM_DATA_SOURCE AS target
    USING (
        SELECT * FROM VALUES
            ('Zillow ZORI', 'Zillow', 'Rent Index', 'Monthly', 'API', 9, 'Zillow Observed Rent Index for metros', 'https://www.zillow.com/research/', TRUE),
            ('ApartmentList', 'ApartmentList', 'Rent Index', 'Monthly', 'Web Scraping', 8, 'Apartment List rent estimates by geography', 'https://www.apartmentlist.com/research/', TRUE),
            ('FRED CPI', 'Federal Reserve', 'Economic Indicator', 'Monthly', 'API', 10, 'Consumer Price Index from Federal Reserve Economic Data', 'https://fred.stlouisfed.org/', TRUE)
        AS source(SOURCE_NAME, SOURCE_SYSTEM, DATA_TYPE, UPDATE_FREQUENCY, COLLECTION_METHOD, RELIABILITY_SCORE, DESCRIPTION, WEBSITE_URL, IS_ACTIVE)
    ) AS source
    ON target.SOURCE_NAME = source.SOURCE_NAME
    WHEN MATCHED THEN UPDATE SET
        SOURCE_SYSTEM = source.SOURCE_SYSTEM,
        DATA_TYPE = source.DATA_TYPE,
        UPDATE_FREQUENCY = source.UPDATE_FREQUENCY,
        COLLECTION_METHOD = source.COLLECTION_METHOD,
        RELIABILITY_SCORE = source.RELIABILITY_SCORE,
        DESCRIPTION = source.DESCRIPTION,
        WEBSITE_URL = source.WEBSITE_URL,
        IS_ACTIVE = source.IS_ACTIVE,
        UPDATED_DATE = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT (
        SOURCE_NAME, SOURCE_SYSTEM, DATA_TYPE, UPDATE_FREQUENCY, COLLECTION_METHOD, 
        RELIABILITY_SCORE, DESCRIPTION, WEBSITE_URL, IS_ACTIVE
    ) VALUES (
        source.SOURCE_NAME, source.SOURCE_SYSTEM, source.DATA_TYPE, source.UPDATE_FREQUENCY, 
        source.COLLECTION_METHOD, source.RELIABILITY_SCORE, source.DESCRIPTION, 
        source.WEBSITE_URL, source.IS_ACTIVE
    );
    
    RETURN 'Data source dimension loaded successfully';
END;
$$;

-- ============================================================================
-- SCD TYPE 2 PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SP_LOAD_DIM_LOCATION_SCD2: Load location dimension with SCD Type 2
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_LOCATION_SCD2()
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    rows_inserted INT := 0;
    rows_updated INT := 0;
    result_msg STRING;
BEGIN
    -- Create staging table with source data
    CREATE OR REPLACE TEMPORARY TABLE STG_LOCATION AS
    WITH source_data AS (
        -- Union data from all source tables
        SELECT DISTINCT
            COALESCE(LOCATION_FIPS_CODE, 'UNKNOWN') AS LOCATION_FIPS_CODE,
            REGIONID AS REGION_ID,
            LOCATION_NAME,
            LOCATION_TYPE,
            STATE AS STATE_NAME,
            LEFT(STATE, 2) AS STATE_CODE,  -- Assuming state is full name, adjust if needed
            COUNTY,
            METRO,
            NULL AS SIZE_RANK,
            POPULATION,
            CURRENT_DATE() AS EFFECTIVE_DATE
        FROM RENTS.RAW.APTLIST_LONG
        WHERE LOCATION_NAME IS NOT NULL
        
        UNION ALL
        
        SELECT DISTINCT
            NULL AS LOCATION_FIPS_CODE,
            REGIONID AS REGION_ID,
            METRO AS LOCATION_NAME,
            REGION_TYPE AS LOCATION_TYPE,
            STATE_NAME,
            LEFT(STATE_NAME, 2) AS STATE_CODE,
            NULL AS COUNTY,
            METRO,
            SIZERANK AS SIZE_RANK,
            NULL AS POPULATION,
            CURRENT_DATE() AS EFFECTIVE_DATE
        FROM RENTS.RAW.ZORI_METRO_LONG
        WHERE METRO IS NOT NULL
    ),
    deduped_source AS (
        SELECT 
            *,
            SHA2(
                CONCAT(
                    COALESCE(LOCATION_FIPS_CODE, ''),
                    COALESCE(REGION_ID::STRING, ''),
                    COALESCE(LOCATION_NAME, ''),
                    COALESCE(LOCATION_TYPE, '')
                )
            ) AS LOCATION_HASH,
            SHA2(
                CONCAT(
                    COALESCE(LOCATION_NAME, ''),
                    COALESCE(LOCATION_TYPE, ''),
                    COALESCE(STATE_NAME, ''),
                    COALESCE(COUNTY, ''),
                    COALESCE(METRO, ''),
                    COALESCE(SIZE_RANK::STRING, ''),
                    COALESCE(POPULATION::STRING, '')
                )
            ) AS ATTRIBUTE_HASH
        FROM source_data
        QUALIFY ROW_NUMBER() OVER (PARTITION BY LOCATION_HASH ORDER BY EFFECTIVE_DATE) = 1
    )
    SELECT * FROM deduped_source;
    
    -- End-date current records that have changed
    UPDATE DIM_LOCATION
    SET 
        END_DATE = CURRENT_DATE() - 1,
        IS_CURRENT = FALSE,
        UPDATED_DATE = CURRENT_TIMESTAMP()
    WHERE IS_CURRENT = TRUE
    AND LOCATION_HASH IN (
        SELECT s.LOCATION_HASH 
        FROM STG_LOCATION s
        JOIN DIM_LOCATION d ON s.LOCATION_HASH = d.LOCATION_HASH AND d.IS_CURRENT = TRUE
        WHERE SHA2(
            CONCAT(
                COALESCE(d.LOCATION_NAME, ''),
                COALESCE(d.LOCATION_TYPE, ''),
                COALESCE(d.STATE_NAME, ''),
                COALESCE(d.COUNTY_NAME, ''),
                COALESCE(d.METRO_NAME, ''),
                COALESCE(d.SIZE_RANK::STRING, ''),
                COALESCE(d.POPULATION::STRING, '')
            )
        ) != s.ATTRIBUTE_HASH
    );
    
    -- Insert new/changed records
    INSERT INTO DIM_LOCATION (
        LOCATION_FIPS_CODE,
        REGION_ID,
        LOCATION_HASH,
        LOCATION_NAME,
        LOCATION_TYPE,
        STATE_CODE,
        STATE_NAME,
        COUNTY_NAME,
        METRO_NAME,
        SIZE_RANK,
        POPULATION,
        EFFECTIVE_DATE,
        END_DATE,
        IS_CURRENT
    )
    SELECT 
        s.LOCATION_FIPS_CODE,
        s.REGION_ID,
        s.LOCATION_HASH,
        s.LOCATION_NAME,
        s.LOCATION_TYPE,
        s.STATE_CODE,
        s.STATE_NAME,
        s.COUNTY,
        s.METRO,
        s.SIZE_RANK,
        s.POPULATION,
        s.EFFECTIVE_DATE,
        NULL AS END_DATE,
        TRUE AS IS_CURRENT
    FROM STG_LOCATION s
    LEFT JOIN DIM_LOCATION d ON s.LOCATION_HASH = d.LOCATION_HASH AND d.IS_CURRENT = TRUE
    WHERE d.LOCATION_KEY IS NULL  -- New records
    OR SHA2(  -- Changed records
        CONCAT(
            COALESCE(d.LOCATION_NAME, ''),
            COALESCE(d.LOCATION_TYPE, ''),
            COALESCE(d.STATE_NAME, ''),
            COALESCE(d.COUNTY_NAME, ''),
            COALESCE(d.METRO_NAME, ''),
            COALESCE(d.SIZE_RANK::STRING, ''),
            COALESCE(d.POPULATION::STRING, '')
        )
    ) != s.ATTRIBUTE_HASH;
    
    rows_inserted := (SELECT COUNT(*) FROM STG_LOCATION);
    result_msg := 'Location dimension SCD2 load completed. Processed ' || rows_inserted || ' records.';
    
    DROP TABLE STG_LOCATION;
    RETURN result_msg;
END;
$$;

-- ----------------------------------------------------------------------------
-- SP_LOAD_DIM_ECONOMIC_SERIES_SCD2: Load economic series with SCD Type 2
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_ECONOMIC_SERIES_SCD2()
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    result_msg STRING;
BEGIN
    -- Create staging table with source data
    CREATE OR REPLACE TEMPORARY TABLE STG_ECONOMIC_SERIES AS
    WITH source_data AS (
        SELECT DISTINCT
            SERIES_ID,
            LABEL AS SERIES_LABEL,
            CASE 
                WHEN UPPER(LABEL) LIKE '%HOUSING%' OR UPPER(LABEL) LIKE '%SHELTER%' THEN 'Housing CPI'
                WHEN UPPER(LABEL) LIKE '%CORE%' THEN 'Core CPI'
                WHEN UPPER(LABEL) LIKE '%ALL ITEMS%' THEN 'All Items CPI'
                ELSE 'Other CPI'
            END AS CATEGORY,
            'CPI Component' AS SUBCATEGORY,
            'Monthly' AS FREQUENCY,
            'Index' AS UNITS,
            'SA' AS SEASONAL_ADJUSTMENT,  -- Assume seasonally adjusted
            '1982-84=100' AS BASE_PERIOD, -- Standard CPI base
            MIN(MONTH) OVER (PARTITION BY SERIES_ID) AS DATA_START_DATE,
            LABEL AS DESCRIPTION,
            CURRENT_DATE() AS EFFECTIVE_DATE,
            TRUE AS IS_ACTIVE
        FROM RENTS.RAW.FRED_CPI_LONG
        WHERE SERIES_ID IS NOT NULL AND LABEL IS NOT NULL
    )
    SELECT 
        *,
        SHA2(
            CONCAT(
                COALESCE(SERIES_LABEL, ''),
                COALESCE(CATEGORY, ''),
                COALESCE(SUBCATEGORY, ''),
                COALESCE(FREQUENCY, ''),
                COALESCE(UNITS, ''),
                COALESCE(SEASONAL_ADJUSTMENT, ''),
                COALESCE(BASE_PERIOD, ''),
                COALESCE(DESCRIPTION, '')
            )
        ) AS ATTRIBUTE_HASH
    FROM source_data;
    
    -- End-date current records that have changed
    UPDATE DIM_ECONOMIC_SERIES
    SET 
        END_DATE = CURRENT_DATE() - 1,
        IS_CURRENT = FALSE,
        UPDATED_DATE = CURRENT_TIMESTAMP()
    WHERE IS_CURRENT = TRUE
    AND SERIES_ID IN (
        SELECT s.SERIES_ID 
        FROM STG_ECONOMIC_SERIES s
        JOIN DIM_ECONOMIC_SERIES d ON s.SERIES_ID = d.SERIES_ID AND d.IS_CURRENT = TRUE
        WHERE SHA2(
            CONCAT(
                COALESCE(d.SERIES_LABEL, ''),
                COALESCE(d.CATEGORY, ''),
                COALESCE(d.SUBCATEGORY, ''),
                COALESCE(d.FREQUENCY, ''),
                COALESCE(d.UNITS, ''),
                COALESCE(d.SEASONAL_ADJUSTMENT, ''),
                COALESCE(d.BASE_PERIOD, ''),
                COALESCE(d.DESCRIPTION, '')
            )
        ) != s.ATTRIBUTE_HASH
    );
    
    -- Insert new/changed records
    INSERT INTO DIM_ECONOMIC_SERIES (
        SERIES_ID,
        SERIES_LABEL,
        CATEGORY,
        SUBCATEGORY,
        FREQUENCY,
        UNITS,
        SEASONAL_ADJUSTMENT,
        BASE_PERIOD,
        DATA_START_DATE,
        DESCRIPTION,
        EFFECTIVE_DATE,
        END_DATE,
        IS_CURRENT,
        IS_ACTIVE
    )
    SELECT 
        s.SERIES_ID,
        s.SERIES_LABEL,
        s.CATEGORY,
        s.SUBCATEGORY,
        s.FREQUENCY,
        s.UNITS,
        s.SEASONAL_ADJUSTMENT,
        s.BASE_PERIOD,
        s.DATA_START_DATE,
        s.DESCRIPTION,
        s.EFFECTIVE_DATE,
        NULL AS END_DATE,
        TRUE AS IS_CURRENT,
        s.IS_ACTIVE
    FROM STG_ECONOMIC_SERIES s
    LEFT JOIN DIM_ECONOMIC_SERIES d ON s.SERIES_ID = d.SERIES_ID AND d.IS_CURRENT = TRUE
    WHERE d.SERIES_KEY IS NULL  -- New records
    OR SHA2(  -- Changed records
        CONCAT(
            COALESCE(d.SERIES_LABEL, ''),
            COALESCE(d.CATEGORY, ''),
            COALESCE(d.SUBCATEGORY, ''),
            COALESCE(d.FREQUENCY, ''),
            COALESCE(d.UNITS, ''),
            COALESCE(d.SEASONAL_ADJUSTMENT, ''),
            COALESCE(d.BASE_PERIOD, ''),
            COALESCE(d.DESCRIPTION, '')
        )
    ) != s.ATTRIBUTE_HASH;
    
    result_msg := 'Economic series dimension SCD2 load completed. Processed ' || (SELECT COUNT(*) FROM STG_ECONOMIC_SERIES) || ' records.';
    
    DROP TABLE STG_ECONOMIC_SERIES;
    RETURN result_msg;
END;
$$;

-- ============================================================================
-- FACT TABLE LOADING PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SP_LOAD_FACT_RENT_ZORI: Load Zillow rent facts with calculated measures
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_RENT_ZORI(
    LOAD_DATE_FROM DATE DEFAULT NULL,
    LOAD_DATE_TO DATE DEFAULT NULL
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    result_msg STRING;
    rows_processed INT;
BEGIN
    -- Set default date range if not provided
    IF (LOAD_DATE_FROM IS NULL) THEN
        LOAD_DATE_FROM := DATEADD('MONTH', -13, DATE_TRUNC('MONTH', CURRENT_DATE()));
    END IF;
    
    IF (LOAD_DATE_TO IS NULL) THEN
        LOAD_DATE_TO := DATE_TRUNC('MONTH', CURRENT_DATE());
    END IF;
    
    -- Delete existing data for the date range
    DELETE FROM FACT_RENT_ZORI 
    WHERE MONTH_DATE >= LOAD_DATE_FROM 
    AND MONTH_DATE <= LOAD_DATE_TO;
    
    -- Insert new fact data with calculated measures
    INSERT INTO FACT_RENT_ZORI (
        TIME_KEY,
        LOCATION_KEY,
        SOURCE_KEY,
        REGIONID,
        MONTH_DATE,
        ZORI_VALUE,
        SIZE_RANK,
        YOY_CHANGE,
        YOY_PCT_CHANGE,
        MOM_CHANGE,
        MOM_PCT_CHANGE,
        RECORD_COUNT,
        DATA_QUALITY_SCORE,
        HAS_ANOMALY,
        SOURCE_FILE_NAME
    )
    WITH fact_data AS (
        SELECT 
            f.*,
            -- Calculate year-over-year changes
            f.ZORI - LAG(f.ZORI, 12) OVER (PARTITION BY f.REGIONID ORDER BY f.MONTH) AS YOY_CHANGE,
            ROUND(
                (f.ZORI - LAG(f.ZORI, 12) OVER (PARTITION BY f.REGIONID ORDER BY f.MONTH)) / 
                NULLIF(LAG(f.ZORI, 12) OVER (PARTITION BY f.REGIONID ORDER BY f.MONTH), 0) * 100, 
                2
            ) AS YOY_PCT_CHANGE,
            -- Calculate month-over-month changes
            f.ZORI - LAG(f.ZORI, 1) OVER (PARTITION BY f.REGIONID ORDER BY f.MONTH) AS MOM_CHANGE,
            ROUND(
                (f.ZORI - LAG(f.ZORI, 1) OVER (PARTITION BY f.REGIONID ORDER BY f.MONTH)) / 
                NULLIF(LAG(f.ZORI, 1) OVER (PARTITION BY f.REGIONID ORDER BY f.MONTH), 0) * 100, 
                2
            ) AS MOM_PCT_CHANGE,
            -- Data quality scoring
            CASE 
                WHEN f.ZORI IS NULL THEN 1
                WHEN f.ZORI <= 0 THEN 2
                WHEN f.ZORI > 10000 THEN 5  -- Flag very high values
                ELSE 10
            END AS DATA_QUALITY_SCORE,
            -- Anomaly detection (simple outlier check)
            ABS(f.ZORI - AVG(f.ZORI) OVER (PARTITION BY f.REGIONID ORDER BY f.MONTH ROWS BETWEEN 5 PRECEDING AND 5 FOLLOWING)) > 
            2 * STDDEV(f.ZORI) OVER (PARTITION BY f.REGIONID ORDER BY f.MONTH ROWS BETWEEN 5 PRECEDING AND 5 FOLLOWING) AS HAS_ANOMALY
        FROM RENTS.RAW.ZORI_METRO_LONG f
        WHERE f.MONTH >= LOAD_DATE_FROM 
        AND f.MONTH <= LOAD_DATE_TO
        AND f.ZORI IS NOT NULL
    )
    SELECT 
        YEAR(fd.MONTH) * 100 + MONTH(fd.MONTH) AS TIME_KEY,
        dl.LOCATION_KEY,
        ds.SOURCE_KEY,
        fd.REGIONID,
        fd.MONTH AS MONTH_DATE,
        fd.ZORI AS ZORI_VALUE,
        fd.SIZERANK AS SIZE_RANK,
        fd.YOY_CHANGE,
        fd.YOY_PCT_CHANGE,
        fd.MOM_CHANGE,
        fd.MOM_PCT_CHANGE,
        1 AS RECORD_COUNT,
        fd.DATA_QUALITY_SCORE,
        fd.HAS_ANOMALY,
        'zori_metro_long.csv' AS SOURCE_FILE_NAME
    FROM fact_data fd
    JOIN DIM_LOCATION dl ON fd.REGIONID = dl.REGION_ID 
        AND fd.MONTH BETWEEN dl.EFFECTIVE_DATE AND COALESCE(dl.END_DATE, CURRENT_DATE())
    JOIN DIM_DATA_SOURCE ds ON ds.SOURCE_NAME = 'Zillow ZORI'
    JOIN DIM_TIME dt ON YEAR(fd.MONTH) * 100 + MONTH(fd.MONTH) = dt.TIME_KEY;
    
    rows_processed := ROW_COUNT;
    result_msg := 'FACT_RENT_ZORI loaded successfully. Processed ' || rows_processed || ' records for date range ' || LOAD_DATE_FROM || ' to ' || LOAD_DATE_TO;
    
    RETURN result_msg;
END;
$$;

-- ----------------------------------------------------------------------------
-- SP_LOAD_FACT_RENT_APTLIST: Load ApartmentList rent facts
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_RENT_APTLIST(
    LOAD_DATE_FROM DATE DEFAULT NULL,
    LOAD_DATE_TO DATE DEFAULT NULL
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    result_msg STRING;
    rows_processed INT;
BEGIN
    -- Set default date range if not provided
    IF (LOAD_DATE_FROM IS NULL) THEN
        LOAD_DATE_FROM := DATEADD('MONTH', -13, DATE_TRUNC('MONTH', CURRENT_DATE()));
    END IF;
    
    IF (LOAD_DATE_TO IS NULL) THEN
        LOAD_DATE_TO := DATE_TRUNC('MONTH', CURRENT_DATE());
    END IF;
    
    -- Delete existing data for the date range
    DELETE FROM FACT_RENT_APTLIST 
    WHERE MONTH_DATE >= LOAD_DATE_FROM 
    AND MONTH_DATE <= LOAD_DATE_TO;
    
    -- Insert new fact data with calculated measures
    INSERT INTO FACT_RENT_APTLIST (
        TIME_KEY,
        LOCATION_KEY,
        SOURCE_KEY,
        LOCATION_FIPS_CODE,
        MONTH_DATE,
        RENT_INDEX,
        POPULATION,
        YOY_CHANGE,
        YOY_PCT_CHANGE,
        MOM_CHANGE,
        MOM_PCT_CHANGE,
        RECORD_COUNT,
        DATA_QUALITY_SCORE,
        HAS_ANOMALY,
        SOURCE_FILE_NAME
    )
    WITH fact_data AS (
        SELECT 
            f.*,
            -- Calculate year-over-year changes
            f.RENT_INDEX - LAG(f.RENT_INDEX, 12) OVER (PARTITION BY f.LOCATION_FIPS_CODE ORDER BY f.MONTH) AS YOY_CHANGE,
            ROUND(
                (f.RENT_INDEX - LAG(f.RENT_INDEX, 12) OVER (PARTITION BY f.LOCATION_FIPS_CODE ORDER BY f.MONTH)) / 
                NULLIF(LAG(f.RENT_INDEX, 12) OVER (PARTITION BY f.LOCATION_FIPS_CODE ORDER BY f.MONTH), 0) * 100, 
                2
            ) AS YOY_PCT_CHANGE,
            -- Calculate month-over-month changes
            f.RENT_INDEX - LAG(f.RENT_INDEX, 1) OVER (PARTITION BY f.LOCATION_FIPS_CODE ORDER BY f.MONTH) AS MOM_CHANGE,
            ROUND(
                (f.RENT_INDEX - LAG(f.RENT_INDEX, 1) OVER (PARTITION BY f.LOCATION_FIPS_CODE ORDER BY f.MONTH)) / 
                NULLIF(LAG(f.RENT_INDEX, 1) OVER (PARTITION BY f.LOCATION_FIPS_CODE ORDER BY f.MONTH), 0) * 100, 
                2
            ) AS MOM_PCT_CHANGE,
            -- Data quality scoring
            CASE 
                WHEN f.RENT_INDEX IS NULL THEN 1
                WHEN f.RENT_INDEX <= 0 THEN 2
                WHEN f.RENT_INDEX > 1000 THEN 5  -- Flag very high index values
                ELSE 10
            END AS DATA_QUALITY_SCORE,
            -- Anomaly detection
            ABS(f.RENT_INDEX - AVG(f.RENT_INDEX) OVER (PARTITION BY f.LOCATION_FIPS_CODE ORDER BY f.MONTH ROWS BETWEEN 5 PRECEDING AND 5 FOLLOWING)) > 
            2 * STDDEV(f.RENT_INDEX) OVER (PARTITION BY f.LOCATION_FIPS_CODE ORDER BY f.MONTH ROWS BETWEEN 5 PRECEDING AND 5 FOLLOWING) AS HAS_ANOMALY
        FROM RENTS.RAW.APTLIST_LONG f
        WHERE f.MONTH >= LOAD_DATE_FROM 
        AND f.MONTH <= LOAD_DATE_TO
        AND f.RENT_INDEX IS NOT NULL
    )
    SELECT 
        YEAR(fd.MONTH) * 100 + MONTH(fd.MONTH) AS TIME_KEY,
        dl.LOCATION_KEY,
        ds.SOURCE_KEY,
        fd.LOCATION_FIPS_CODE,
        fd.MONTH AS MONTH_DATE,
        fd.RENT_INDEX,
        fd.POPULATION,
        fd.YOY_CHANGE,
        fd.YOY_PCT_CHANGE,
        fd.MOM_CHANGE,
        fd.MOM_PCT_CHANGE,
        1 AS RECORD_COUNT,
        fd.DATA_QUALITY_SCORE,
        fd.HAS_ANOMALY,
        'apartmentlist_long.csv' AS SOURCE_FILE_NAME
    FROM fact_data fd
    JOIN DIM_LOCATION dl ON COALESCE(fd.LOCATION_FIPS_CODE, 'UNKNOWN') = COALESCE(dl.LOCATION_FIPS_CODE, 'UNKNOWN')
        AND fd.MONTH BETWEEN dl.EFFECTIVE_DATE AND COALESCE(dl.END_DATE, CURRENT_DATE())
    JOIN DIM_DATA_SOURCE ds ON ds.SOURCE_NAME = 'ApartmentList'
    JOIN DIM_TIME dt ON YEAR(fd.MONTH) * 100 + MONTH(fd.MONTH) = dt.TIME_KEY;
    
    rows_processed := ROW_COUNT;
    result_msg := 'FACT_RENT_APTLIST loaded successfully. Processed ' || rows_processed || ' records for date range ' || LOAD_DATE_FROM || ' to ' || LOAD_DATE_TO;
    
    RETURN result_msg;
END;
$$;

-- ----------------------------------------------------------------------------
-- SP_LOAD_FACT_ECONOMIC_INDICATOR: Load economic indicator facts
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_ECONOMIC_INDICATOR(
    LOAD_DATE_FROM DATE DEFAULT NULL,
    LOAD_DATE_TO DATE DEFAULT NULL
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    result_msg STRING;
    rows_processed INT;
BEGIN
    -- Set default date range if not provided
    IF (LOAD_DATE_FROM IS NULL) THEN
        LOAD_DATE_FROM := DATEADD('MONTH', -13, DATE_TRUNC('MONTH', CURRENT_DATE()));
    END IF;
    
    IF (LOAD_DATE_TO IS NULL) THEN
        LOAD_DATE_TO := DATE_TRUNC('MONTH', CURRENT_DATE());
    END IF;
    
    -- Delete existing data for the date range
    DELETE FROM FACT_ECONOMIC_INDICATOR 
    WHERE MONTH_DATE >= LOAD_DATE_FROM 
    AND MONTH_DATE <= LOAD_DATE_TO;
    
    -- Insert new fact data with calculated measures
    INSERT INTO FACT_ECONOMIC_INDICATOR (
        TIME_KEY,
        SERIES_KEY,
        SOURCE_KEY,
        SERIES_ID,
        MONTH_DATE,
        INDICATOR_VALUE,
        YOY_CHANGE,
        YOY_PCT_CHANGE,
        MOM_CHANGE,
        MOM_PCT_CHANGE,
        RECORD_COUNT,
        DATA_QUALITY_SCORE,
        IS_REVISED,
        REVISION_COUNT,
        SOURCE_FILE_NAME
    )
    WITH fact_data AS (
        SELECT 
            f.*,
            -- Calculate year-over-year changes
            f.VALUE - LAG(f.VALUE, 12) OVER (PARTITION BY f.SERIES_ID ORDER BY f.MONTH) AS YOY_CHANGE,
            ROUND(
                (f.VALUE - LAG(f.VALUE, 12) OVER (PARTITION BY f.SERIES_ID ORDER BY f.MONTH)) / 
                NULLIF(LAG(f.VALUE, 12) OVER (PARTITION BY f.SERIES_ID ORDER BY f.MONTH), 0) * 100, 
                2
            ) AS YOY_PCT_CHANGE,
            -- Calculate month-over-month changes
            f.VALUE - LAG(f.VALUE, 1) OVER (PARTITION BY f.SERIES_ID ORDER BY f.MONTH) AS MOM_CHANGE,
            ROUND(
                (f.VALUE - LAG(f.VALUE, 1) OVER (PARTITION BY f.SERIES_ID ORDER BY f.MONTH)) / 
                NULLIF(LAG(f.VALUE, 1) OVER (PARTITION BY f.SERIES_ID ORDER BY f.MONTH), 0) * 100, 
                2
            ) AS MOM_PCT_CHANGE,
            -- Data quality scoring
            CASE 
                WHEN f.VALUE IS NULL THEN 1
                WHEN f.VALUE < 0 THEN 3  -- Negative values might be valid for some series
                ELSE 10
            END AS DATA_QUALITY_SCORE
        FROM RENTS.RAW.FRED_CPI_LONG f
        WHERE f.MONTH >= LOAD_DATE_FROM 
        AND f.MONTH <= LOAD_DATE_TO
        AND f.VALUE IS NOT NULL
    )
    SELECT 
        YEAR(fd.MONTH) * 100 + MONTH(fd.MONTH) AS TIME_KEY,
        des.SERIES_KEY,
        ds.SOURCE_KEY,
        fd.SERIES_ID,
        fd.MONTH AS MONTH_DATE,
        fd.VALUE AS INDICATOR_VALUE,
        fd.YOY_CHANGE,
        fd.YOY_PCT_CHANGE,
        fd.MOM_CHANGE,
        fd.MOM_PCT_CHANGE,
        1 AS RECORD_COUNT,
        fd.DATA_QUALITY_SCORE,
        FALSE AS IS_REVISED,  -- TODO: Implement revision tracking
        0 AS REVISION_COUNT,
        'fred_cpi_long.csv' AS SOURCE_FILE_NAME
    FROM fact_data fd
    JOIN DIM_ECONOMIC_SERIES des ON fd.SERIES_ID = des.SERIES_ID 
        AND fd.MONTH BETWEEN des.EFFECTIVE_DATE AND COALESCE(des.END_DATE, CURRENT_DATE())
    JOIN DIM_DATA_SOURCE ds ON ds.SOURCE_NAME = 'FRED CPI'
    JOIN DIM_TIME dt ON YEAR(fd.MONTH) * 100 + MONTH(fd.MONTH) = dt.TIME_KEY;
    
    rows_processed := ROW_COUNT;
    result_msg := 'FACT_ECONOMIC_INDICATOR loaded successfully. Processed ' || rows_processed || ' records for date range ' || LOAD_DATE_FROM || ' to ' || LOAD_DATE_TO;
    
    RETURN result_msg;
END;
$$;

-- ============================================================================
-- MASTER ETL ORCHESTRATION PROCEDURE
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SP_FULL_ETL_PROCESS: Complete ETL orchestration
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_FULL_ETL_PROCESS(
    LOAD_DATE_FROM DATE DEFAULT NULL,
    LOAD_DATE_TO DATE DEFAULT NULL
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    result_msg STRING := '';
    step_result STRING;
BEGIN
    result_msg := 'Starting full ETL process...\n';
    
    -- Step 1: Generate time dimension
    CALL SP_GENERATE_TIME_DIMENSION();
    result_msg := result_msg || 'Step 1: Time dimension generated\n';
    
    -- Step 2: Load data source dimension
    CALL SP_LOAD_DIM_DATA_SOURCE();
    result_msg := result_msg || 'Step 2: Data source dimension loaded\n';
    
    -- Step 3: Load location dimension with SCD Type 2
    CALL SP_LOAD_DIM_LOCATION_SCD2();
    result_msg := result_msg || 'Step 3: Location dimension (SCD2) loaded\n';
    
    -- Step 4: Load economic series dimension with SCD Type 2
    CALL SP_LOAD_DIM_ECONOMIC_SERIES_SCD2();
    result_msg := result_msg || 'Step 4: Economic series dimension (SCD2) loaded\n';
    
    -- Step 5: Load Zillow rent facts
    CALL SP_LOAD_FACT_RENT_ZORI(LOAD_DATE_FROM, LOAD_DATE_TO);
    result_msg := result_msg || 'Step 5: Zillow rent facts loaded\n';
    
    -- Step 6: Load ApartmentList rent facts
    CALL SP_LOAD_FACT_RENT_APTLIST(LOAD_DATE_FROM, LOAD_DATE_TO);
    result_msg := result_msg || 'Step 6: ApartmentList rent facts loaded\n';
    
    -- Step 7: Load economic indicator facts
    CALL SP_LOAD_FACT_ECONOMIC_INDICATOR(LOAD_DATE_FROM, LOAD_DATE_TO);
    result_msg := result_msg || 'Step 7: Economic indicator facts loaded\n';
    
    result_msg := result_msg || '\nFull ETL process completed successfully!';
    RETURN result_msg;
END;
$$;