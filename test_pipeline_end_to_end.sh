#!/bin/bash
# ============================================================================
# End-to-End Pipeline Test Script
# Tests complete GitHub → S3 → Snowflake flow for rent signals data
# ============================================================================

set -euo pipefail

# Configuration
BUCKET="${RENT_SIGNALS_BUCKET:-rent-signals-dev-dd}"
TODAY=$(date -u +%F)

echo "🚀 End-to-End Pipeline Test"
echo "==========================="
echo "Bucket: $BUCKET"
echo "Date: $TODAY"
echo ""

# ============================================================================
# STEP 1: Test Local Scripts
# ============================================================================

echo "🔧 Step 1: Testing local conversion scripts..."

# Test Zillow conversion script
if [[ -f "scripts/zillow_wide_to_long.py" ]]; then
    echo "Testing Zillow wide-to-long conversion..."
    
    # Download sample data
    mkdir -p test_data
    URL="https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv"
    curl -fsSL "$URL" -o test_data/sample_wide.csv
    
    # Test conversion
    python scripts/zillow_wide_to_long.py test_data/sample_wide.csv test_data/sample_long.csv
    
    if [[ -f "test_data/sample_long.csv" ]]; then
        echo "✅ Zillow conversion successful"
        echo "Sample output:"
        head -n 3 test_data/sample_long.csv
    else
        echo "❌ Zillow conversion failed"
        exit 1
    fi
else
    echo "❌ Zillow conversion script not found"
    exit 1
fi

# Test ApartmentList download script
if [[ -f "scripts/download_apartmentlist.py" ]]; then
    echo "✅ ApartmentList download script found"
else
    echo "❌ ApartmentList download script not found"
fi

echo ""

# ============================================================================
# STEP 2: Test GitHub Actions Workflows
# ============================================================================

echo "📋 Step 2: Checking GitHub Actions workflows..."

# Check workflow files exist
workflows=("aptlist_to_s3.yml" "zori_metro_to_s3.yml" "fred_to_s3.yml")
for workflow in "${workflows[@]}"; do
    if [[ -f ".github/workflows/$workflow" ]]; then
        echo "✅ Workflow found: $workflow"
    else
        echo "❌ Workflow missing: $workflow"
    fi
done

echo ""
echo "To test workflows manually:"
echo "1. Go to GitHub Actions tab"
echo "2. Select 'Update Zillow Metro CSV to S3' workflow"
echo "3. Click 'Run workflow' button"
echo "4. Monitor execution and check for errors"

echo ""

# ============================================================================
# STEP 3: Test S3 Access and Current Data
# ============================================================================

echo "☁️ Step 3: Testing S3 access and current data..."

# Check AWS credentials
if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "✅ AWS credentials configured"
    aws sts get-caller-identity | grep -E "(Account|Arn)"
else
    echo "❌ AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

# Check bucket access
if aws s3 ls "s3://$BUCKET/" >/dev/null 2>&1; then
    echo "✅ S3 bucket accessible: $BUCKET"
else
    echo "❌ Cannot access S3 bucket: $BUCKET"
    exit 1
fi

# List recent data
echo ""
echo "Recent data in S3:"

# Check ApartmentList data
echo "ApartmentList data:"
aws s3 ls "s3://$BUCKET/aptlist/" --recursive | tail -5 || echo "No ApartmentList data found"

# Check Zillow data  
echo "Zillow data:"
aws s3 ls "s3://$BUCKET/zillow/" --recursive | tail -5 || echo "No Zillow data found"

# Check FRED data
echo "FRED data:"
aws s3 ls "s3://$BUCKET/fred/" --recursive | tail -5 || echo "No FRED data found"

echo ""

# ============================================================================
# STEP 4: Generate Test Data if Missing
# ============================================================================

echo "📦 Step 4: Ensuring test data exists..."

# Upload test Zillow data if missing
if ! aws s3 ls "s3://$BUCKET/zillow/metro/$TODAY/" >/dev/null 2>&1; then
    echo "Uploading test Zillow data for today..."
    
    mkdir -p standardized
    if [[ -f "test_data/sample_long.csv" ]]; then
        aws s3 cp test_data/sample_long.csv "s3://$BUCKET/zillow/metro/$TODAY/zori_metro_long.csv"
        echo "✅ Uploaded test Zillow long format data"
    else
        echo "❌ No test data to upload"
    fi
else
    echo "✅ Zillow data exists for today"
fi

echo ""

# ============================================================================
# STEP 5: Test Snowflake Connectivity (if available)
# ============================================================================

echo "❄️ Step 5: Snowflake connectivity test..."

if command -v snowsql >/dev/null 2>&1; then
    echo "SnowSQL CLI found - testing connection..."
    
    # Test basic connection (requires snowsql to be configured)
    if snowsql -q "SELECT CURRENT_VERSION();" >/dev/null 2>&1; then
        echo "✅ Snowflake connection successful"
        
        # Test stage access
        echo "Testing stage access..."
        snowsql -q "LIST @S3_ZORI_METRO_STAGE/$TODAY/;" 2>/dev/null || \
        echo "⚠️ Stage access test failed - run debug_snowflake_csv.sql manually"
        
    else
        echo "❌ Snowflake connection failed"
        echo "Configure with: snowsql -c <connection_name>"
    fi
else
    echo "⚠️ SnowSQL CLI not installed"
    echo "Install from: https://docs.snowflake.com/en/user-guide/snowsql-install-config.html"
    echo "Or run debug_snowflake_csv.sql manually in Snowflake console"
fi

echo ""

# ============================================================================
# STEP 6: Summary and Next Steps
# ============================================================================

echo "📊 Step 6: Test Summary"
echo "======================="

echo "✅ Completed checks:"
echo "  - Local conversion scripts"
echo "  - GitHub Actions workflow files"
echo "  - S3 bucket access"
echo "  - AWS credentials"

echo ""
echo "📋 Manual steps required:"
echo "  1. Run GitHub Actions workflows manually to generate fresh data"
echo "  2. Execute debug_snowflake_csv.sql in Snowflake console"
echo "  3. Execute snowflake_setup.sql to create proper stages and tables"
echo "  4. Test COPY INTO commands with the generated data"

echo ""
echo "🔧 Debug tools available:"
echo "  - ./debug_csv_locally.sh - Inspect CSV files from S3"
echo "  - debug_snowflake_csv.sql - Comprehensive Snowflake debugging"
echo "  - snowflake_setup.sql - Updated setup with named file formats"

echo ""
echo "🎯 Success criteria:"
echo "  - GitHub Actions workflows run without errors"
echo "  - CSV files appear in S3 with expected structure"
echo "  - Snowflake can SELECT from external stages"
echo "  - COPY INTO commands load data successfully"
echo "  - Tables contain expected row counts and data types"

# Cleanup
rm -rf test_data

echo ""
echo "🏁 End-to-end test completed!"
echo "Review the output above and run manual steps as needed."