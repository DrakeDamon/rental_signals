#!/bin/bash
# ============================================================================
# Local CSV Inspection Script
# Downloads and validates Zillow CSV files for Snowflake pipeline debugging
# ============================================================================

set -euo pipefail

# Configuration
BUCKET="rent-signals-dev-dd"
TODAY=$(date -u +%F)
YESTERDAY=$(date -u -d '1 day ago' +%F)
LOCAL_DIR="debug_csv"

echo "🔍 CSV Pipeline Debug Script"
echo "============================"
echo "Bucket: $BUCKET"
echo "Today: $TODAY"
echo "Yesterday: $YESTERDAY"
echo ""

# Create local debug directory
mkdir -p "$LOCAL_DIR"
cd "$LOCAL_DIR"

# ============================================================================
# STEP 1: Download Latest Zillow Files from S3
# ============================================================================

echo "📥 Step 1: Downloading files from S3..."

# Try today's files first, then yesterday's
for date in "$TODAY" "$YESTERDAY"; do
    echo "Checking files for date: $date"
    
    # List files for this date
    echo "Listing S3 files:"
    aws s3 ls "s3://$BUCKET/zillow/metro/$date/" || continue
    
    # Download wide format
    if aws s3 cp "s3://$BUCKET/zillow/metro/$date/zori_metro_wide.csv" "./zori_metro_wide_${date}.csv" 2>/dev/null; then
        echo "✅ Downloaded wide format for $date"
        WIDE_FILE="./zori_metro_wide_${date}.csv"
    else
        echo "❌ No wide format file for $date"
    fi
    
    # Download long format  
    if aws s3 cp "s3://$BUCKET/zillow/metro/$date/zori_metro_long.csv" "./zori_metro_long_${date}.csv" 2>/dev/null; then
        echo "✅ Downloaded long format for $date"
        LONG_FILE="./zori_metro_long_${date}.csv"
    else
        echo "❌ No long format file for $date"
    fi
    
    # If we found files, use this date
    if [[ -n "${WIDE_FILE:-}" ]] || [[ -n "${LONG_FILE:-}" ]]; then
        ACTIVE_DATE="$date"
        break
    fi
done

if [[ -z "${ACTIVE_DATE:-}" ]]; then
    echo "❌ No CSV files found for recent dates. Downloading fresh data..."
    
    # Download fresh data from Zillow
    echo "📦 Downloading fresh Zillow data..."
    URL="https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv"
    curl -fsSL "$URL" -o "zori_metro_wide_fresh.csv"
    WIDE_FILE="./zori_metro_wide_fresh.csv"
    echo "✅ Downloaded fresh wide format"
fi

echo ""

# ============================================================================
# STEP 2: Inspect File Structure
# ============================================================================

echo "🔬 Step 2: Inspecting CSV file structure..."

if [[ -n "${WIDE_FILE:-}" ]] && [[ -f "$WIDE_FILE" ]]; then
    echo "📄 Wide Format File: $WIDE_FILE"
    echo "File size: $(ls -lh "$WIDE_FILE" | awk '{print $5}')"
    echo "Line count: $(wc -l < "$WIDE_FILE")"
    echo ""
    
    echo "First 3 lines:"
    head -n 3 "$WIDE_FILE"
    echo ""
    
    echo "Header analysis:"
    head -n 1 "$WIDE_FILE" | tr ',' '\n' | nl -v0 | head -20
    echo "... (showing first 20 columns)"
    
    # Count total columns
    COL_COUNT=$(head -n 1 "$WIDE_FILE" | tr ',' '\n' | wc -l)
    echo "Total columns: $COL_COUNT"
    echo ""
    
    # Check for date columns
    echo "Date columns detected:"
    head -n 1 "$WIDE_FILE" | tr ',' '\n' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | head -10
    echo ""
fi

if [[ -n "${LONG_FILE:-}" ]] && [[ -f "$LONG_FILE" ]]; then
    echo "📄 Long Format File: $LONG_FILE"
    echo "File size: $(ls -lh "$LONG_FILE" | awk '{print $5}')"
    echo "Line count: $(wc -l < "$LONG_FILE")"
    echo ""
    
    echo "First 5 lines:"
    head -n 5 "$LONG_FILE"
    echo ""
    
    echo "Header analysis:"
    head -n 1 "$LONG_FILE" | tr ',' '\n' | nl -v0
    
    # Count total columns
    COL_COUNT=$(head -n 1 "$LONG_FILE" | tr ',' '\n' | wc -l)
    echo "Total columns: $COL_COUNT"
    echo ""
fi

# ============================================================================
# STEP 3: Python Validation
# ============================================================================

echo "🐍 Step 3: Python pandas validation..."

python3 << 'EOF'
import pandas as pd
import sys
from pathlib import Path

# Find CSV files
wide_files = list(Path('.').glob('*wide*.csv'))
long_files = list(Path('.').glob('*long*.csv'))

print(f"Found {len(wide_files)} wide files: {[f.name for f in wide_files]}")
print(f"Found {len(long_files)} long files: {[f.name for f in long_files]}")
print()

# Test wide format
for wide_file in wide_files:
    print(f"📊 Testing wide format: {wide_file.name}")
    try:
        df = pd.read_csv(wide_file)
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
        
        # Check for date columns
        date_cols = [col for col in df.columns if pd.to_datetime(col, errors='coerce') is not pd.NaT]
        print(f"  Date columns found: {len(date_cols)}")
        if date_cols:
            print(f"  Date range: {min(date_cols)} to {max(date_cols)}")
        
        # Check data types
        print("  Data types:")
        for col in df.columns[:5]:
            print(f"    {col}: {df[col].dtype}")
        
        print()
        
    except Exception as e:
        print(f"  ❌ Error reading wide format: {e}")
        print()

# Test long format  
for long_file in long_files:
    print(f"📊 Testing long format: {long_file.name}")
    try:
        df = pd.read_csv(long_file)
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        
        # Check expected schema
        expected_cols = ['REGIONID', 'SIZERANK', 'METRO', 'REGION_TYPE', 'STATE_NAME', 'month', 'zori']
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            print(f"  ❌ Missing expected columns: {missing_cols}")
        else:
            print(f"  ✅ All expected columns present")
        
        # Check data types and sample data
        print("  Data types and samples:")
        for col in df.columns:
            dtype = df[col].dtype
            sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else 'N/A'
            print(f"    {col}: {dtype} (sample: {sample})")
        
        # Check for nulls
        null_counts = df.isnull().sum()
        if null_counts.any():
            print("  Null value counts:")
            for col, count in null_counts[null_counts > 0].items():
                print(f"    {col}: {count}")
        
        print()
        
    except Exception as e:
        print(f"  ❌ Error reading long format: {e}")
        print()
EOF

# ============================================================================
# STEP 4: Generate Conversion Test
# ============================================================================

if [[ -n "${WIDE_FILE:-}" ]] && [[ -f "$WIDE_FILE" ]] && [[ -z "${LONG_FILE:-}" ]]; then
    echo "🔄 Step 4: Testing wide-to-long conversion..."
    
    # Test the conversion script
    if [[ -f "../scripts/zillow_wide_to_long.py" ]]; then
        echo "Running conversion script..."
        python3 ../scripts/zillow_wide_to_long.py "$WIDE_FILE" "converted_long.csv"
        
        if [[ -f "converted_long.csv" ]]; then
            echo "✅ Conversion successful!"
            echo "First 5 lines of converted file:"
            head -n 5 "converted_long.csv"
        else
            echo "❌ Conversion failed - no output file"
        fi
    else
        echo "❌ Conversion script not found at ../scripts/zillow_wide_to_long.py"
    fi
fi

# ============================================================================
# STEP 5: Summary and Recommendations
# ============================================================================

echo ""
echo "📋 Summary and Recommendations"
echo "============================="

if [[ -n "${WIDE_FILE:-}" ]] && [[ -f "$WIDE_FILE" ]]; then
    echo "✅ Wide format file available and readable"
else
    echo "❌ Wide format file missing or unreadable"
fi

if [[ -n "${LONG_FILE:-}" ]] && [[ -f "$LONG_FILE" ]]; then
    echo "✅ Long format file available and readable"
else
    echo "❌ Long format file missing - needs conversion"
fi

echo ""
echo "Next steps:"
echo "1. Run the Snowflake debug script: debug_snowflake_csv.sql"
echo "2. If Snowflake can't read the CSV, check file format settings"
echo "3. Ensure GitHub Actions workflow is uploading the correct long format file"
echo "4. Use the COPY INTO command with explicit column mapping"

echo ""
echo "Files available for inspection:"
ls -la *.csv 2>/dev/null || echo "No CSV files in debug directory"