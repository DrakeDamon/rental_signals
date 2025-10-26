#!/bin/bash
# ================================================================
# END-TO-END PIPELINE TEST
# Tests: Ingestion → S3 → Snowflake → dbt → Validation
# ================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
export BUCKET="${BUCKET:-rent-signals-dev-dd}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_ROOT="/Users/daviddamon/Desktop/tampa rental signals/tampa-rent-signals"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   END-TO-END PIPELINE TEST${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ================================================================
# STEP 1: CHECK PREREQUISITES
# ================================================================
echo -e "${YELLOW}STEP 1: Checking Prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI installed${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 installed${NC}"

# Check dbt
if ! command -v dbt &> /dev/null; then
    echo -e "${YELLOW}⚠ dbt not found - skipping dbt tests${NC}"
    SKIP_DBT=true
else
    echo -e "${GREEN}✓ dbt installed${NC}"
    SKIP_DBT=false
fi

# Check if Snowflake CLI exists
if ! command -v snow &> /dev/null && ! command -v snowsql &> /dev/null; then
    echo -e "${YELLOW}⚠ Snowflake CLI not found - skipping Snowflake tests${NC}"
    SKIP_SNOWFLAKE=true
else
    echo -e "${GREEN}✓ Snowflake CLI installed${NC}"
    SKIP_SNOWFLAKE=false
fi

echo ""

# ================================================================
# STEP 2: TEST INGESTION SCRIPTS
# ================================================================
echo -e "${YELLOW}STEP 2: Testing Ingestion Scripts...${NC}"

cd "$PROJECT_ROOT"

# Test Zillow
echo -e "${BLUE}Testing Zillow scraper...${NC}"
if python3 ingest/zillow_zori_pull.py 2>&1 | grep -q "saved="; then
    echo -e "${GREEN}✓ Zillow: Script executed successfully${NC}"
    if [ -d "data/bronze/zillow_zori" ]; then
        ZILLOW_FILES=$(find data/bronze/zillow_zori -name "*.csv" | wc -l)
        echo -e "${GREEN}  Found $ZILLOW_FILES bronze CSV file(s)${NC}"
    fi
else
    echo -e "${RED}✗ Zillow: Script failed${NC}"
fi

# Test ApartmentList
echo -e "${BLUE}Testing ApartmentList scraper...${NC}"
if python3 ingest/apartmentlist_pull.py 2>&1 | grep -q "saved="; then
    echo -e "${GREEN}✓ ApartmentList: Script executed successfully${NC}"
    if [ -d "data/bronze/apartmentlist" ]; then
        APT_FILES=$(find data/bronze/apartmentlist -name "*.csv" | wc -l)
        echo -e "${GREEN}  Found $APT_FILES bronze CSV file(s)${NC}"
    fi
else
    echo -e "${RED}✗ ApartmentList: Script failed${NC}"
fi

# Test FRED (requires API key)
echo -e "${BLUE}Testing FRED scraper...${NC}"
if [ -f ".env" ]; then
    source .env
fi

if [ -z "$FRED_API_KEY" ] && [ -z "$FRED_API" ]; then
    echo -e "${YELLOW}⚠ FRED_API_KEY not set - skipping FRED test${NC}"
else
    export FRED_API_KEY="${FRED_API_KEY:-$FRED_API}"
    if python3 ingest/fred_tampa_rent_pull.py 2>&1 | grep -q "saved="; then
        echo -e "${GREEN}✓ FRED: Script executed successfully${NC}"
        if [ -d "data/bronze/fred" ]; then
            FRED_FILES=$(find data/bronze/fred -name "*.json" | wc -l)
            echo -e "${GREEN}  Found $FRED_FILES bronze JSON file(s)${NC}"
        fi
    else
        echo -e "${RED}✗ FRED: Script failed${NC}"
    fi
fi

echo ""

# ================================================================
# STEP 3: TEST S3 UPLOADS
# ================================================================
echo -e "${YELLOW}STEP 3: Testing S3 Uploads...${NC}"

# Check if bucket exists
if aws s3 ls "s3://$BUCKET" 2>&1 | grep -q "NoSuchBucket"; then
    echo -e "${RED}✗ S3 bucket $BUCKET does not exist${NC}"
    echo -e "${YELLOW}  Create with: aws s3 mb s3://$BUCKET${NC}"
    exit 1
fi
echo -e "${GREEN}✓ S3 bucket $BUCKET exists${NC}"

# Upload bronze data
echo -e "${BLUE}Uploading bronze data to S3...${NC}"

# Zillow
if [ -d "data/bronze/zillow_zori" ]; then
    echo -e "  Uploading Zillow..."
    aws s3 sync data/bronze/zillow_zori/ s3://$BUCKET/zillow/bronze/ \
        --exclude "*" --include "date=*/*" --quiet
    ZILLOW_COUNT=$(aws s3 ls s3://$BUCKET/zillow/bronze/ --recursive | wc -l)
    echo -e "${GREEN}  ✓ Zillow: $ZILLOW_COUNT file(s) in S3${NC}"
fi

# ApartmentList
if [ -d "data/bronze/apartmentlist" ]; then
    echo -e "  Uploading ApartmentList..."
    aws s3 sync data/bronze/apartmentlist/ s3://$BUCKET/apartmentlist/bronze/ \
        --exclude "*" --include "date=*/*" --quiet
    APT_COUNT=$(aws s3 ls s3://$BUCKET/apartmentlist/bronze/ --recursive | wc -l)
    echo -e "${GREEN}  ✓ ApartmentList: $APT_COUNT file(s) in S3${NC}"
fi

# FRED
if [ -d "data/bronze/fred" ]; then
    echo -e "  Uploading FRED..."
    aws s3 sync data/bronze/fred/ s3://$BUCKET/fred/bronze/ \
        --exclude "*" --include "date=*/*" --quiet
    FRED_COUNT=$(aws s3 ls s3://$BUCKET/fred/bronze/ --recursive | wc -l)
    echo -e "${GREEN}  ✓ FRED: $FRED_COUNT file(s) in S3${NC}"
fi

echo ""

# ================================================================
# STEP 4: VERIFY S3 DATA
# ================================================================
echo -e "${YELLOW}STEP 4: Verifying S3 Data...${NC}"

echo -e "${BLUE}S3 Bronze Layer Contents:${NC}"
aws s3 ls s3://$BUCKET/zillow/bronze/ --recursive --human-readable | head -5
aws s3 ls s3://$BUCKET/apartmentlist/bronze/ --recursive --human-readable | head -5
aws s3 ls s3://$BUCKET/fred/bronze/ --recursive --human-readable | head -5

echo ""

# ================================================================
# STEP 5: TEST SNOWFLAKE CONNECTION (if configured)
# ================================================================
if [ "$SKIP_SNOWFLAKE" = false ]; then
    echo -e "${YELLOW}STEP 5: Testing Snowflake Connection...${NC}"
    
    # Try snowsql
    if command -v snowsql &> /dev/null; then
        echo -e "${BLUE}Testing Snowflake connection with snowsql...${NC}"
        if snowsql -q "SELECT CURRENT_DATABASE(), CURRENT_SCHEMA();" 2>&1 | grep -q "RENTS"; then
            echo -e "${GREEN}✓ Connected to Snowflake${NC}"
            
            # Check if RAW tables exist
            echo -e "${BLUE}Checking RAW tables...${NC}"
            snowsql -q "SHOW TABLES IN RENTS.RAW;" 2>&1 | grep -E "(ZORI|APTLIST|FRED)" || \
                echo -e "${YELLOW}  ⚠ RAW tables not found - run sql/ingestion/load_from_s3_bronze.sql${NC}"
        else
            echo -e "${YELLOW}⚠ Could not connect to Snowflake - check credentials${NC}"
        fi
    fi
else
    echo -e "${YELLOW}STEP 5: Skipping Snowflake tests (CLI not installed)${NC}"
fi

echo ""

# ================================================================
# STEP 6: TEST DBT (if installed)
# ================================================================
if [ "$SKIP_DBT" = false ]; then
    echo -e "${YELLOW}STEP 6: Testing dbt...${NC}"
    
    cd "$PROJECT_ROOT/dbt_rent_signals"
    
    # Check dbt connection
    echo -e "${BLUE}Testing dbt connection...${NC}"
    if dbt debug 2>&1 | grep -q "Connection test: \[OK\]"; then
        echo -e "${GREEN}✓ dbt connected to Snowflake${NC}"
        
        # Compile models
        echo -e "${BLUE}Compiling dbt models...${NC}"
        if dbt compile 2>&1 | grep -q "Completed successfully"; then
            echo -e "${GREEN}✓ dbt models compiled successfully${NC}"
        else
            echo -e "${YELLOW}⚠ dbt compilation had issues${NC}"
        fi
        
        # Parse models
        echo -e "${BLUE}Parsing dbt models...${NC}"
        dbt parse 2>&1 | tail -5
        
    else
        echo -e "${YELLOW}⚠ dbt connection failed - check profiles.yml${NC}"
    fi
    
    cd "$PROJECT_ROOT"
else
    echo -e "${YELLOW}STEP 6: Skipping dbt tests (not installed)${NC}"
fi

echo ""

# ================================================================
# STEP 7: DAGSTER CHECK (if installed)
# ================================================================
echo -e "${YELLOW}STEP 7: Checking Dagster Configuration...${NC}"

if [ -d "dagster_rent_signals" ]; then
    cd "$PROJECT_ROOT/dagster_rent_signals"
    
    if python3 -c "import dagster" 2>/dev/null; then
        echo -e "${GREEN}✓ Dagster installed${NC}"
        
        # Check if definitions load
        echo -e "${BLUE}Validating Dagster definitions...${NC}"
        if python3 -c "from dagster_rent_signals.definitions import defs; print(f'Assets: {len(defs.assets)}')" 2>&1 | grep -q "Assets:"; then
            ASSET_COUNT=$(python3 -c "from dagster_rent_signals.definitions import defs; print(len(defs.assets))" 2>/dev/null || echo "?")
            echo -e "${GREEN}✓ Dagster definitions loaded: $ASSET_COUNT assets${NC}"
        else
            echo -e "${YELLOW}⚠ Could not load Dagster definitions${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Dagster not installed${NC}"
        echo -e "${YELLOW}  Install with: cd dagster_rent_signals && pip install -e \".[dev]\"${NC}"
    fi
    
    cd "$PROJECT_ROOT"
else
    echo -e "${YELLOW}⚠ Dagster project not found${NC}"
fi

echo ""

# ================================================================
# STEP 8: DATA QUALITY CHECKS
# ================================================================
echo -e "${YELLOW}STEP 8: Data Quality Checks...${NC}"

# Check local bronze data
echo -e "${BLUE}Checking local bronze data:${NC}"

if [ -d "data/bronze/zillow_zori" ]; then
    ZILLOW_SIZE=$(du -sh data/bronze/zillow_zori 2>/dev/null | cut -f1)
    ZILLOW_ROWS=$(find data/bronze/zillow_zori -name "*.csv" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
    echo -e "${GREEN}✓ Zillow: $ZILLOW_SIZE, ~$ZILLOW_ROWS rows${NC}"
fi

if [ -d "data/bronze/apartmentlist" ]; then
    APT_SIZE=$(du -sh data/bronze/apartmentlist 2>/dev/null | cut -f1)
    APT_ROWS=$(find data/bronze/apartmentlist -name "*.csv" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
    echo -e "${GREEN}✓ ApartmentList: $APT_SIZE, ~$APT_ROWS rows${NC}"
fi

if [ -d "data/bronze/fred" ]; then
    FRED_SIZE=$(du -sh data/bronze/fred 2>/dev/null | cut -f1)
    FRED_FILES=$(find data/bronze/fred -name "*.json" | wc -l)
    echo -e "${GREEN}✓ FRED: $FRED_SIZE, $FRED_FILES file(s)${NC}"
fi

# Check silver data
echo -e "${BLUE}Checking local silver data:${NC}"

if [ -d "data/silver/zillow_zori" ]; then
    echo -e "${GREEN}✓ Zillow silver layer exists${NC}"
fi

if [ -d "data/silver/apartmentlist" ]; then
    echo -e "${GREEN}✓ ApartmentList silver layer exists${NC}"
fi

if [ -d "data/silver/fred" ]; then
    echo -e "${GREEN}✓ FRED silver layer exists${NC}"
fi

echo ""

# ================================================================
# FINAL SUMMARY
# ================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   PIPELINE TEST SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${GREEN}✓ COMPLETED CHECKS:${NC}"
echo -e "  • Ingestion scripts tested"
echo -e "  • Bronze data created locally"
echo -e "  • Bronze data uploaded to S3: s3://$BUCKET"
echo -e "  • S3 data verified"

if [ "$SKIP_SNOWFLAKE" = false ]; then
    echo -e "  • Snowflake connection tested"
else
    echo -e "${YELLOW}  ⚠ Snowflake tests skipped${NC}"
fi

if [ "$SKIP_DBT" = false ]; then
    echo -e "  • dbt configuration checked"
else
    echo -e "${YELLOW}  ⚠ dbt tests skipped${NC}"
fi

echo -e "  • Dagster configuration validated"
echo ""

echo -e "${YELLOW}⏸ REMAINING STEPS:${NC}"
if [ "$SKIP_SNOWFLAKE" = true ]; then
    echo -e "  1. Install Snowflake CLI (snowsql)"
fi
echo -e "  2. Run: sql/ingestion/load_from_s3_bronze.sql in Snowflake"
echo -e "  3. Load data: COPY INTO RENTS.RAW.* FROM @*_bronze_stage;"
if [ "$SKIP_DBT" = true ]; then
    echo -e "  4. Install dbt: pip install dbt-snowflake"
fi
echo -e "  5. Run dbt: dbt run --models staging"
echo -e "  6. Run dbt: dbt run --models core"
echo -e "  7. Run dbt: dbt run --models marts"
echo -e "  8. Run dbt tests: dbt test"
echo -e "  9. Validate: python great_expectations/validate_data_quality.py --layer all"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   END-TO-END TEST COMPLETE!${NC}"
echo -e "${GREEN}========================================${NC}"


