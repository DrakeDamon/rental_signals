-- ============================================================================
-- RENT SIGNALS DATA WAREHOUSE - ANALYTICS SCHEMA
-- Star Schema with SCD Type 2 Implementation
-- ============================================================================

-- Create Analytics Schema
CREATE SCHEMA IF NOT EXISTS RENTS.ANALYTICS;
USE SCHEMA RENTS.ANALYTICS;

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- DIM_TIME: Central time dimension (SCD Type 0 - Static)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE DIM_TIME (
    TIME_KEY                INT PRIMARY KEY,           -- YYYYMM format: 202510
    MONTH_DATE              DATE NOT NULL,             -- 2025-10-01
    YEAR                    INT NOT NULL,              -- 2025
    QUARTER                 INT NOT NULL,              -- 4
    MONTH_NUMBER            INT NOT NULL,              -- 10
    MONTH_NAME              VARCHAR(20) NOT NULL,      -- 'October'
    QUARTER_NAME            VARCHAR(10) NOT NULL,      -- 'Q4 2025'
    FISCAL_YEAR             INT NOT NULL,              -- 2026 (Oct-Sep fiscal year)
    IS_CURRENT_MONTH        BOOLEAN NOT NULL,          -- TRUE for current month
    MONTHS_AGO              INT NOT NULL,              -- 0=current, 1=last month
    
    -- Metadata
    CREATED_DATE            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT CK_TIME_VALID_MONTH CHECK (MONTH_NUMBER BETWEEN 1 AND 12),
    CONSTRAINT CK_TIME_VALID_QUARTER CHECK (QUARTER BETWEEN 1 AND 4)
);

-- ----------------------------------------------------------------------------
-- DIM_LOCATION: Geographic dimension (SCD Type 2 - Historical tracking)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE DIM_LOCATION (
    LOCATION_KEY            INT IDENTITY(1,1) PRIMARY KEY,  -- Surrogate key
    
    -- Business Keys
    LOCATION_FIPS_CODE      VARCHAR(20),                    -- FIPS code
    REGION_ID               INT,                            -- Zillow region ID
    LOCATION_HASH           VARCHAR(64) NOT NULL,           -- Hash of business key combo
    
    -- Location Attributes (these can change over time - SCD Type 2)
    LOCATION_NAME           VARCHAR(200) NOT NULL,
    LOCATION_TYPE           VARCHAR(50) NOT NULL,           -- 'metro', 'county', 'state', 'country'
    STATE_CODE              VARCHAR(2),                     -- 'NY', 'CA'
    STATE_NAME              VARCHAR(100),                   -- 'New York', 'California'
    COUNTY_NAME             VARCHAR(100),                   -- County name
    METRO_NAME              VARCHAR(200),                   -- Metro area name
    SIZE_RANK               INT,                            -- Zillow size ranking
    POPULATION              INT,                            -- Population estimate
    
    -- SCD Type 2 Fields
    EFFECTIVE_DATE          DATE NOT NULL,                  -- When this version became active
    END_DATE                DATE,                           -- When this version ended (NULL = current)
    IS_CURRENT              BOOLEAN NOT NULL DEFAULT TRUE,  -- TRUE for current version
    
    -- Metadata
    CREATED_DATE            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_DATE            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT CK_LOCATION_VALID_SCD CHECK (
        (IS_CURRENT = TRUE AND END_DATE IS NULL) OR 
        (IS_CURRENT = FALSE AND END_DATE IS NOT NULL)
    ),
    CONSTRAINT CK_LOCATION_VALID_DATES CHECK (EFFECTIVE_DATE <= COALESCE(END_DATE, CURRENT_DATE()))
);

-- ----------------------------------------------------------------------------
-- DIM_ECONOMIC_SERIES: Economic indicator metadata (SCD Type 2)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE DIM_ECONOMIC_SERIES (
    SERIES_KEY              INT IDENTITY(1,1) PRIMARY KEY,  -- Surrogate key
    
    -- Business Key
    SERIES_ID               VARCHAR(50) NOT NULL,           -- FRED series ID
    
    -- Series Attributes (can change over time - SCD Type 2)
    SERIES_LABEL            VARCHAR(500) NOT NULL,          -- Human-readable name
    CATEGORY                VARCHAR(100),                   -- 'Housing CPI', 'Core CPI'
    SUBCATEGORY             VARCHAR(100),                   -- More granular classification
    FREQUENCY               VARCHAR(20),                    -- 'Monthly', 'Quarterly'
    UNITS                   VARCHAR(100),                   -- 'Index', 'Percent Change'
    SEASONAL_ADJUSTMENT     VARCHAR(10),                    -- 'SA', 'NSA'
    BASE_PERIOD             VARCHAR(50),                    -- '1982-84=100'
    DATA_START_DATE         DATE,                           -- When series began
    DESCRIPTION             TEXT,                           -- Detailed description
    
    -- SCD Type 2 Fields
    EFFECTIVE_DATE          DATE NOT NULL,
    END_DATE                DATE,
    IS_CURRENT              BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Metadata
    IS_ACTIVE               BOOLEAN NOT NULL DEFAULT TRUE,  -- For soft deletes
    CREATED_DATE            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_DATE            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT CK_SERIES_VALID_SCD CHECK (
        (IS_CURRENT = TRUE AND END_DATE IS NULL) OR 
        (IS_CURRENT = FALSE AND END_DATE IS NOT NULL)
    )
);

-- ----------------------------------------------------------------------------
-- DIM_DATA_SOURCE: Source system metadata (SCD Type 1 - Overwrite changes)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE DIM_DATA_SOURCE (
    SOURCE_KEY              INT IDENTITY(1,1) PRIMARY KEY,  -- Surrogate key
    SOURCE_NAME             VARCHAR(100) NOT NULL UNIQUE,   -- 'Zillow ZORI', 'ApartmentList'
    SOURCE_SYSTEM           VARCHAR(100) NOT NULL,          -- 'Zillow', 'ApartmentList', 'FRED'
    DATA_TYPE               VARCHAR(100) NOT NULL,          -- 'Rent Index', 'Economic Indicator'
    UPDATE_FREQUENCY        VARCHAR(50),                    -- 'Monthly', 'Daily'
    COLLECTION_METHOD       VARCHAR(100),                   -- 'API', 'Web Scraping'
    RELIABILITY_SCORE       INT,                            -- 1-10 data quality rating
    DESCRIPTION             TEXT,
    WEBSITE_URL             VARCHAR(500),
    
    -- Metadata
    IS_ACTIVE               BOOLEAN NOT NULL DEFAULT TRUE,
    CREATED_DATE            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_DATE            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT CK_SOURCE_RELIABILITY CHECK (RELIABILITY_SCORE BETWEEN 1 AND 10)
);

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- FACT_RENT_ZORI: Zillow rent index facts (Monthly grain)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE FACT_RENT_ZORI (
    -- Dimension Foreign Keys
    TIME_KEY                INT NOT NULL,
    LOCATION_KEY            INT NOT NULL,
    SOURCE_KEY              INT NOT NULL,
    
    -- Business Keys (for debugging/validation)
    REGIONID                INT NOT NULL,
    MONTH_DATE              DATE NOT NULL,
    
    -- Measures
    ZORI_VALUE              DECIMAL(12,2) NOT NULL,         -- Primary rent index
    SIZE_RANK               INT,                            -- Metro size ranking
    YOY_CHANGE              DECIMAL(12,2),                  -- Year-over-year change ($)
    YOY_PCT_CHANGE          DECIMAL(8,2),                   -- Year-over-year change (%)
    MOM_CHANGE              DECIMAL(12,2),                  -- Month-over-month change ($)
    MOM_PCT_CHANGE          DECIMAL(8,2),                   -- Month-over-month change (%)
    RECORD_COUNT            INT NOT NULL DEFAULT 1,         -- Always 1, for aggregation
    
    -- Data Quality
    DATA_QUALITY_SCORE      INT,                            -- 1-10 quality rating
    HAS_ANOMALY             BOOLEAN DEFAULT FALSE,          -- Outlier detection flag
    
    -- Metadata
    LOAD_DATE               TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    SOURCE_FILE_NAME        VARCHAR(500),                   -- For data lineage
    
    -- Constraints
    CONSTRAINT FK_ZORI_TIME FOREIGN KEY (TIME_KEY) REFERENCES DIM_TIME(TIME_KEY),
    CONSTRAINT FK_ZORI_LOCATION FOREIGN KEY (LOCATION_KEY) REFERENCES DIM_LOCATION(LOCATION_KEY),
    CONSTRAINT FK_ZORI_SOURCE FOREIGN KEY (SOURCE_KEY) REFERENCES DIM_DATA_SOURCE(SOURCE_KEY),
    CONSTRAINT CK_ZORI_QUALITY CHECK (DATA_QUALITY_SCORE BETWEEN 1 AND 10),
    CONSTRAINT CK_ZORI_POSITIVE_VALUE CHECK (ZORI_VALUE > 0)
);

-- ----------------------------------------------------------------------------
-- FACT_RENT_APTLIST: ApartmentList rent facts (Monthly grain)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE FACT_RENT_APTLIST (
    -- Dimension Foreign Keys
    TIME_KEY                INT NOT NULL,
    LOCATION_KEY            INT NOT NULL,
    SOURCE_KEY              INT NOT NULL,
    
    -- Business Keys
    LOCATION_FIPS_CODE      VARCHAR(20),
    MONTH_DATE              DATE NOT NULL,
    
    -- Measures
    RENT_INDEX              DECIMAL(12,2) NOT NULL,         -- Primary rent metric
    POPULATION              INT,                            -- Population estimate
    YOY_CHANGE              DECIMAL(12,2),                  -- Year-over-year change
    YOY_PCT_CHANGE          DECIMAL(8,2),                   -- Year-over-year change (%)
    MOM_CHANGE              DECIMAL(12,2),                  -- Month-over-month change
    MOM_PCT_CHANGE          DECIMAL(8,2),                   -- Month-over-month change (%)
    RECORD_COUNT            INT NOT NULL DEFAULT 1,
    
    -- Data Quality
    DATA_QUALITY_SCORE      INT,
    HAS_ANOMALY             BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    LOAD_DATE               TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    SOURCE_FILE_NAME        VARCHAR(500),
    
    -- Constraints
    CONSTRAINT FK_APTLIST_TIME FOREIGN KEY (TIME_KEY) REFERENCES DIM_TIME(TIME_KEY),
    CONSTRAINT FK_APTLIST_LOCATION FOREIGN KEY (LOCATION_KEY) REFERENCES DIM_LOCATION(LOCATION_KEY),
    CONSTRAINT FK_APTLIST_SOURCE FOREIGN KEY (SOURCE_KEY) REFERENCES DIM_DATA_SOURCE(SOURCE_KEY),
    CONSTRAINT CK_APTLIST_QUALITY CHECK (DATA_QUALITY_SCORE BETWEEN 1 AND 10),
    CONSTRAINT CK_APTLIST_POSITIVE_INDEX CHECK (RENT_INDEX > 0)
);

-- ----------------------------------------------------------------------------
-- FACT_ECONOMIC_INDICATOR: Economic metrics (Monthly grain)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE FACT_ECONOMIC_INDICATOR (
    -- Dimension Foreign Keys
    TIME_KEY                INT NOT NULL,
    SERIES_KEY              INT NOT NULL,
    SOURCE_KEY              INT NOT NULL,
    
    -- Business Keys
    SERIES_ID               VARCHAR(50) NOT NULL,
    MONTH_DATE              DATE NOT NULL,
    
    -- Measures
    INDICATOR_VALUE         DECIMAL(15,4) NOT NULL,         -- Primary economic metric
    YOY_CHANGE              DECIMAL(15,4),                  -- Year-over-year change
    YOY_PCT_CHANGE          DECIMAL(8,2),                   -- Year-over-year change (%)
    MOM_CHANGE              DECIMAL(15,4),                  -- Month-over-month change
    MOM_PCT_CHANGE          DECIMAL(8,2),                   -- Month-over-month change (%)
    RECORD_COUNT            INT NOT NULL DEFAULT 1,
    
    -- Data Quality
    DATA_QUALITY_SCORE      INT,
    IS_REVISED              BOOLEAN DEFAULT FALSE,          -- FRED data revision flag
    REVISION_COUNT          INT DEFAULT 0,                  -- Number of revisions
    
    -- Metadata
    LOAD_DATE               TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    SOURCE_FILE_NAME        VARCHAR(500),
    
    -- Constraints
    CONSTRAINT FK_ECON_TIME FOREIGN KEY (TIME_KEY) REFERENCES DIM_TIME(TIME_KEY),
    CONSTRAINT FK_ECON_SERIES FOREIGN KEY (SERIES_KEY) REFERENCES DIM_ECONOMIC_SERIES(SERIES_KEY),
    CONSTRAINT FK_ECON_SOURCE FOREIGN KEY (SOURCE_KEY) REFERENCES DIM_DATA_SOURCE(SOURCE_KEY),
    CONSTRAINT CK_ECON_QUALITY CHECK (DATA_QUALITY_SCORE BETWEEN 1 AND 10)
);

-- ============================================================================
-- INDEXES AND CLUSTERING
-- ============================================================================

-- Time Dimension Indexes
CREATE INDEX IF NOT EXISTS IDX_TIME_DATE ON DIM_TIME(MONTH_DATE);
CREATE INDEX IF NOT EXISTS IDX_TIME_CURRENT ON DIM_TIME(IS_CURRENT_MONTH);

-- Location Dimension Indexes (SCD Type 2 aware)
CREATE INDEX IF NOT EXISTS IDX_LOCATION_FIPS_CURRENT ON DIM_LOCATION(LOCATION_FIPS_CODE, IS_CURRENT);
CREATE INDEX IF NOT EXISTS IDX_LOCATION_REGION_CURRENT ON DIM_LOCATION(REGION_ID, IS_CURRENT);
CREATE INDEX IF NOT EXISTS IDX_LOCATION_EFFECTIVE_DATE ON DIM_LOCATION(EFFECTIVE_DATE, END_DATE);
CREATE INDEX IF NOT EXISTS IDX_LOCATION_HASH ON DIM_LOCATION(LOCATION_HASH);

-- Economic Series Indexes (SCD Type 2 aware)
CREATE INDEX IF NOT EXISTS IDX_SERIES_ID_CURRENT ON DIM_ECONOMIC_SERIES(SERIES_ID, IS_CURRENT);
CREATE INDEX IF NOT EXISTS IDX_SERIES_EFFECTIVE_DATE ON DIM_ECONOMIC_SERIES(EFFECTIVE_DATE, END_DATE);

-- Fact Table Clustering for Performance
ALTER TABLE FACT_RENT_ZORI CLUSTER BY (TIME_KEY, LOCATION_KEY);
ALTER TABLE FACT_RENT_APTLIST CLUSTER BY (TIME_KEY, LOCATION_KEY);
ALTER TABLE FACT_ECONOMIC_INDICATOR CLUSTER BY (TIME_KEY, SERIES_KEY);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

-- Table Comments
ALTER TABLE DIM_TIME COMMENT = 'Central time dimension with monthly grain. SCD Type 0 (static).';
ALTER TABLE DIM_LOCATION COMMENT = 'Geographic dimension with SCD Type 2 for population and boundary changes.';
ALTER TABLE DIM_ECONOMIC_SERIES COMMENT = 'Economic series metadata with SCD Type 2 for label/category changes.';
ALTER TABLE DIM_DATA_SOURCE COMMENT = 'Source system metadata with SCD Type 1 (overwrite changes).';
ALTER TABLE FACT_RENT_ZORI COMMENT = 'Zillow rent index facts. Grain: one row per metro per month.';
ALTER TABLE FACT_RENT_APTLIST COMMENT = 'ApartmentList rent facts. Grain: one row per location per month.';
ALTER TABLE FACT_ECONOMIC_INDICATOR COMMENT = 'Economic indicator facts. Grain: one row per series per month.';

-- Key Column Comments
ALTER TABLE DIM_LOCATION ALTER COLUMN LOCATION_KEY COMMENT 'Surrogate key for SCD Type 2 support';
ALTER TABLE DIM_LOCATION ALTER COLUMN EFFECTIVE_DATE COMMENT 'When this dimension version became active';
ALTER TABLE DIM_LOCATION ALTER COLUMN END_DATE COMMENT 'When this dimension version ended (NULL = current)';
ALTER TABLE DIM_LOCATION ALTER COLUMN IS_CURRENT COMMENT 'TRUE for current active version';
ALTER TABLE DIM_LOCATION ALTER COLUMN LOCATION_HASH COMMENT 'Hash of business keys for change detection';

ALTER TABLE DIM_ECONOMIC_SERIES ALTER COLUMN SERIES_KEY COMMENT 'Surrogate key for SCD Type 2 support';
ALTER TABLE DIM_ECONOMIC_SERIES ALTER COLUMN EFFECTIVE_DATE COMMENT 'When this series version became active';

-- ============================================================================
-- SAMPLE SCD TYPE 2 JOIN PATTERNS
-- ============================================================================

/*
-- How to join facts to SCD Type 2 dimensions:

-- Join FACT_RENT_ZORI to current location dimension
SELECT f.*, d.LOCATION_NAME, d.POPULATION
FROM FACT_RENT_ZORI f
JOIN DIM_LOCATION d 
  ON f.LOCATION_KEY = d.LOCATION_KEY 
 AND d.IS_CURRENT = TRUE;

-- Join FACT_RENT_ZORI to historical location dimension (as of fact date)
SELECT f.*, d.LOCATION_NAME, d.POPULATION
FROM FACT_RENT_ZORI f
JOIN DIM_LOCATION d 
  ON f.LOCATION_KEY = d.LOCATION_KEY 
 AND f.MONTH_DATE BETWEEN d.EFFECTIVE_DATE AND COALESCE(d.END_DATE, CURRENT_DATE());

-- Join using business key with SCD Type 2 time window
SELECT f.*, d.LOCATION_NAME, d.POPULATION
FROM FACT_RENT_ZORI f
JOIN DIM_LOCATION d 
  ON f.REGIONID = d.REGION_ID 
 AND f.MONTH_DATE BETWEEN d.EFFECTIVE_DATE AND COALESCE(d.END_DATE, CURRENT_DATE())
 AND d.LOCATION_TYPE = 'metro';
*/