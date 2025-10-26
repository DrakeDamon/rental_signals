# ApartmentList Scraper - Test Results & Issues

**Test Date**: October 26, 2025  
**Script**: `ingest/apartmentlist_pull.py`

---

## ⚠️ ISSUE IDENTIFIED: Playwright Required

### Problem

ApartmentList does NOT provide direct CSV download links on their research page. The page uses JavaScript to:

1. Load a dropdown menu with data options
2. Require user interaction to select a dataset
3. Trigger download via JavaScript event

**Investigation Results:**

```
✅ Page loads successfully
❌ No direct .csv links found (0 links)
❌ No "download" links found (0 links)
✅ "Updated September 29, 2025" date found
❌ No file links (.csv, .xlsx, .zip) accessible via simple scraping
```

This is why your existing `scripts/download_apartmentlist.py` uses **Playwright** for browser automation.

---

## ✅ SOLUTION IMPLEMENTED

I've rewritten `ingest/apartmentlist_pull.py` to use Playwright (matching your existing approach), with these enhancements:

### New Features

1. **Browser Automation**

   - Uses Playwright to interact with dropdown
   - Selects "Historic Rent Estimates (Jan 2017 - Present)"
   - Clicks download button
   - Captures CSV file

2. **Bronze/Silver Layers**

   - Bronze: Raw CSV saved to `data/bronze/apartmentlist/date=YYYY-MM/`
   - Silver: Tampa-filtered Parquet to `data/silver/apartmentlist/date=YYYY-MM/`

3. **Tampa Filtering**

   - Tries multiple Tampa name variations:
     - "Tampa-St. Petersburg-Clearwater, FL"
     - "Tampa, FL"
     - "Tampa - St. Petersburg - Clearwater, FL"

4. **Idempotent Operation**

   - Won't re-download if month already exists
   - Use `--force` flag to override

5. **Error Handling**
   - Fallback to response capture if download event fails
   - Helpful error messages
   - Lists available FL metros if Tampa not found

---

## 📋 REQUIREMENTS

### Dependencies Needed

```bash
# Install Playwright
pip install playwright pandas pyarrow python-dateutil

# Install Chromium browser
playwright install chromium
```

### Add to `ingest/requirements.txt`

```txt
# Existing dependencies
requests>=2.32.0
beautifulsoup4>=4.13.0
pandas>=2.1.0
pyarrow>=20.0.0
python-dateutil>=2.9.0

# New: for ApartmentList
playwright>=1.40.0
```

---

## 🧪 TESTING (Once Playwright is Installed)

### Test Command

```bash
cd /path/to/tampa-rent-signals
python ingest/apartmentlist_pull.py
```

### Expected Output

```
Downloading ApartmentList data for 2025-09...
Navigating to https://www.apartmentlist.com/research/category/data-rent-estimates
Selecting option: Historic Rent Estimates (Jan 2017 - Present)
Clicking Download...
Downloaded via download event: apartmentlist_historic_rent_estimates.csv
Processing downloaded file: data/bronze/apartmentlist/date=2025-09/apartmentlist_historic.csv
Found 105 rows for Tampa, FL
apartmentlist: latest=2025-09 rows=105 saved=data/silver/apartmentlist/date=2025-09/apartmentlist_tampa.parquet
```

### Output Files

**Bronze Layer:**

```
data/bronze/apartmentlist/date=2025-09/
└── apartmentlist_historic.csv    # Full US dataset
```

**Silver Layer:**

```
data/silver/apartmentlist/date=2025-09/
└── apartmentlist_tampa.parquet   # Tampa only, tidy format
```

---

## 🔄 COMPARISON: Old vs New

### Old Script (`scripts/download_apartmentlist.py`)

- ✅ Uses Playwright (correct approach)
- ❌ Only saves raw CSV
- ❌ No bronze/silver layer structure
- ❌ No Tampa filtering
- ❌ No idempotency
- ❌ Manual file placement required

### New Script (`ingest/apartmentlist_pull.py`)

- ✅ Uses Playwright (same approach)
- ✅ Bronze layer (raw CSV)
- ✅ Silver layer (Tampa Parquet)
- ✅ Automatic Tampa filtering
- ✅ Idempotent (won't duplicate)
- ✅ Date-partitioned structure
- ✅ Ready for Dagster integration

---

## 🚀 DAGSTER INTEGRATION (READY)

Once Playwright is installed and tested, the script can be integrated into Dagster using the same pattern as Zillow:

### Asset Code (Example)

```python
@asset(
    group_name="ingestion",
    description="Download and process ApartmentList rent estimates for Tampa",
)
def apartmentlist_ingestion(
    context: AssetExecutionContext,
    s3: S3Resource,
) -> Output[dict]:
    """Run ApartmentList ingestion and upload to S3."""

    # Run script
    result = subprocess.run(
        [sys.executable, "ingest/apartmentlist_pull.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    # Parse output, upload to S3, return metadata
    # ... (same pattern as zillow_zori_ingestion)
```

---

## ⚠️ LIMITATIONS & CONSIDERATIONS

### Playwright Overhead

- **Headless browser** required (Chromium ~300 MB download)
- **Slower** than direct HTTP downloads (30-60 seconds vs 3 seconds)
- **More dependencies** to manage
- **Potential for breakage** if ApartmentList changes page structure

### Alternative Approaches

1. **Contact ApartmentList**

   - Request direct API access
   - Ask for stable CSV URLs
   - Request data partnership

2. **Use Existing Downloads**

   - Keep using `scripts/download_apartmentlist.py`
   - Manually copy files to bronze layer
   - Run transformation separately

3. **Selenium Alternative**
   - Use Selenium instead of Playwright
   - May be more stable/familiar
   - Similar overhead

---

## 📊 EXPECTED DATA STRUCTURE

### CSV Columns (ApartmentList)

```
region_type, region_name, region_id, year, month, rent
```

### Silver Layer Output

```
source: "apartmentlist"
region_type: "msa"
region_name: "Tampa, FL" (or variation)
region_id: <integer or NULL>
period: "YYYY-MM"
value: <rent value>
pulled_at: <timestamp>
date: "YYYY-MM" (partition key)
```

---

## ✅ WHAT'S READY

1. ✅ **Script rewritten** to use Playwright + bronze/silver layers
2. ✅ **Error handling** improved with helpful messages
3. ✅ **Multiple Tampa variations** tried automatically
4. ✅ **Idempotent operation** with `--force` option
5. ✅ **Ready for Dagster** (same pattern as Zillow)
6. ✅ **Documentation** provided

## ⏸️ WHAT'S NEEDED

1. ⏸️ **Install Playwright**: `pip install playwright && playwright install chromium`
2. ⏸️ **Test script**: `python ingest/apartmentlist_pull.py`
3. ⏸️ **Verify output**: Check bronze and silver layers
4. ⏸️ **Add to Dagster**: Create `apartmentlist_ingestion` asset
5. ⏸️ **Update schedule**: Include in monthly ingestion job

---

## 🎯 RECOMMENDATION

### Option A: Full Automation (Recommended)

```bash
# 1. Install Playwright
pip install playwright
playwright install chromium

# 2. Test script
python ingest/apartmentlist_pull.py

# 3. Add to ingest/requirements.txt
echo "playwright>=1.40.0" >> ingest/requirements.txt

# 4. Create Dagster asset (copy Zillow pattern)
# 5. Add to monthly schedule
```

### Option B: Manual/Hybrid Approach

```bash
# 1. Use existing script for download
python scripts/download_apartmentlist.py --out temp/apartmentlist.csv

# 2. Copy to bronze layer
mkdir -p data/bronze/apartmentlist/date=2025-09
cp temp/apartmentlist.csv data/bronze/apartmentlist/date=2025-09/

# 3. Run transformation separately
# Create a simpler transform-only script
```

---

## 📝 SUMMARY

**Status**: ⚠️ **Script Ready, Playwright Required**

The ApartmentList scraper has been successfully rewritten to follow the same bronze/silver pattern as Zillow. However, it requires Playwright for browser automation because ApartmentList doesn't provide direct CSV links.

**Next Step**: Install Playwright and test:

```bash
pip install playwright && playwright install chromium
python ingest/apartmentlist_pull.py
```

Once working, it can be integrated into Dagster using the exact same pattern as `zillow_zori_ingestion`.

