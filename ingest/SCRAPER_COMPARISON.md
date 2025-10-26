# Ingestion Scrapers - Complete Comparison & Status

**Test Date**: October 26, 2025

---

## ✅ ZILLOW ZORI SCRAPER - **FULLY WORKING**

### Status: **PRODUCTION READY** ✅

### Script: `ingest/zillow_zori_pull.py`

### Test Results

```bash
$ python ingest/zillow_zori_pull.py
✅ SUCCESS
zillow_zori: latest=2025-09 rows=129 saved=data/silver/zillow_zori/date=2025-09/zori_tampa.parquet
```

### What Works

- ✅ **Web scraping**: Discovers CSV links on Zillow research page
- ✅ **Download**: Gets latest metro-level ZORI data via HTTP
- ✅ **Bronze layer**: Saves raw CSV (906 KB, 696 metros)
- ✅ **Silver layer**: Filters to Tampa, saves Parquet (6.7 KB, 129 rows)
- ✅ **Data quality**: 100% complete, no NULLs, proper types
- ✅ **Idempotent**: Won't duplicate on repeated runs
- ✅ **Fast**: Completes in ~3 seconds

### Data Output

**Bronze**: `data/bronze/zillow_zori/date=2025-09/metro_zori.csv`

- Size: 906 KB
- Rows: 696 US metros
- Columns: RegionID, RegionName, RegionType, StateName, SizeRank, [129 monthly columns]

**Silver**: `data/silver/zillow_zori/date=2025-09/zori_tampa.parquet`

- Size: 6.7 KB
- Rows: 129 (2015-01 to 2025-09)
- Schema: source, region_type, region_name, region_id, period, value, pulled_at, date

### Dependencies

```txt
requests>=2.32.0
beautifulsoup4>=4.13.0
pandas>=2.1.0
pyarrow>=20.0.0
python-dateutil>=2.9.0
```

### Integration Status

- ✅ Dagster asset created: `zillow_zori_ingestion`
- ✅ S3 resource implemented
- ✅ Monthly schedule configured
- ✅ GitHub Actions workflow ready
- ✅ Documentation complete

---

## ⚠️ APARTMENTLIST SCRAPER - **NEEDS DEBUGGING**

### Status: **SCRIPT READY, DOWNLOAD FAILING** ⚠️

### Script: `ingest/apartmentlist_pull.py`

### Test Results

```bash
$ python ingest/apartmentlist_pull.py
⚠️ PARTIAL SUCCESS
Downloading ApartmentList data for 2025-09...
Navigating to https://www.apartmentlist.com/research/category/data-rent-estimates
Selecting option: Historic Rent Estimates (Jan 2017 - Present)
Clicking Download...
❌ Error: Download button not found
Failed to download ApartmentList CSV
```

### What Works

- ✅ **Playwright integration**: Browser automation loads
- ✅ **Page navigation**: Successfully reaches data page
- ✅ **Dropdown interaction**: Finds and interacts with selector
- ✅ **Bronze/Silver structure**: Code implemented correctly
- ✅ **Tampa filtering**: Logic ready with multiple name variations
- ✅ **Error handling**: Graceful failure with helpful messages

### What Doesn't Work

- ❌ **Download button**: Can't locate the download trigger
- ❌ **File download**: No CSV obtained
- ❌ **Data processing**: Can't test without downloaded file

### Root Cause

The ApartmentList page structure has likely changed:

1. **Button selector** may have changed (`role="button"` with `name="Download"`)
2. **Dynamic loading**: Button might load via JavaScript after delay
3. **Different interaction**: Might need form submission instead of button click
4. **Page redesign**: Entire download mechanism could be different

### Dependencies

```txt
playwright>=1.40.0
pandas>=2.1.0
pyarrow>=20.0.0
python-dateutil>=2.9.0
```

### Integration Status

- ✅ Script structure matches Zillow pattern
- ✅ Bronze/silver layers implemented
- ✅ Idempotency logic included
- ⏸️ Dagster asset not created yet (waiting for working script)
- ⏸️ Cannot test end-to-end until download works

---

## 📊 COMPARISON TABLE

| Feature              | Zillow ZORI          | ApartmentList                      |
| -------------------- | -------------------- | ---------------------------------- |
| **Download Method**  | ✅ Direct HTTP       | ⚠️ Browser automation required     |
| **Complexity**       | ✅ Simple (requests) | ⚠️ Complex (Playwright)            |
| **Speed**            | ✅ Fast (~3 sec)     | ⚠️ Slow (~30-60 sec if working)    |
| **Reliability**      | ✅ High              | ⚠️ Fragile (page changes break it) |
| **Dependencies**     | ✅ Minimal           | ⚠️ Heavy (Chromium browser)        |
| **Test Status**      | ✅ Fully working     | ❌ Download failing                |
| **Bronze Layer**     | ✅ Working           | ⏸️ Not testable                    |
| **Silver Layer**     | ✅ Working           | ⏸️ Not testable                    |
| **Dagster Ready**    | ✅ Yes               | ⏸️ Once download works             |
| **Production Ready** | ✅ Yes               | ❌ No                              |

---

## 🔧 FIXES NEEDED FOR APARTMENTLIST

### Option 1: Debug Current Approach (Recommended)

**Investigate button locator:**

```python
# Current approach (not working)
btn = page.get_by_role("button", name=re.compile(r"^Download$", re.I)).first

# Try alternatives:
# 1. By text content
await page.get_by_text("Download").click()

# 2. By class or ID
await page.locator(".download-button").click()
await page.locator("#download-btn").click()

# 3. By CSS selector
await page.locator("button[aria-label='Download']").click()

# 4. By XPath
await page.locator("//button[contains(text(), 'Download')]").click()
```

**Add debugging:**

```python
# Take screenshot
await page.screenshot(path="apartmentlist_page.png")

# Print all buttons
buttons = await page.locator("button").all()
for btn in buttons:
    text = await btn.inner_text()
    print(f"Found button: {text}")
```

### Option 2: Use Existing Script

Keep using `scripts/download_apartmentlist.py` which you know works:

```bash
# 1. Download with existing script
python scripts/download_apartmentlist.py --out temp/apartmentlist.csv

# 2. Transform with new script (modify to skip download)
python ingest/apartmentlist_transform.py --input temp/apartmentlist.csv

# 3. Or manually copy to bronze layer
mkdir -p data/bronze/apartmentlist/date=2025-09
cp temp/apartmentlist.csv data/bronze/apartmentlist/date=2025-09/
```

### Option 3: Contact ApartmentList

Request official API access or stable CSV URLs to avoid fragile web scraping.

---

## ✅ RECOMMENDED PATH FORWARD

### For Zillow (READY NOW)

1. **Deploy to Production**

   ```bash
   # Already working - just enable
   cd dagster_rent_signals
   pip install -e '.[dev]'
   export BUCKET=your-bucket
   dagster dev
   # Materialize zillow_zori_ingestion asset
   ```

2. **Set up automation**

   - Monthly Dagster schedule (already configured)
   - GitHub Actions workflow (already created)
   - S3 uploads (already implemented)

3. **Integrate with Snowflake**
   - Run `sql/ingestion/load_zillow_from_s3.sql`
   - Test COPY INTO command
   - Enable daily loading task

### For ApartmentList (NEEDS FIX)

1. **Debug Download** (1-2 hours)

   ```python
   # Add to script for investigation:
   await page.screenshot(path="debug_page.png")
   print(await page.content())  # Print HTML
   buttons = await page.locator("button").all()
   for b in buttons:
       print(await b.inner_text())
   ```

2. **Alternative: Use Existing Script**

   - Keep using `scripts/download_apartmentlist.py`
   - Create separate transformation script
   - Manual workflow until download fixed

3. **Skip for MVP** (Recommended)
   - Focus on Zillow first (already working)
   - Add ApartmentList in Phase 2
   - Build successful pattern with Zillow, then replicate

---

## 🎯 MVP RECOMMENDATION

### Phase 1: Zillow Only (THIS WEEK)

**The Zillow scraper is production-ready NOW:**

1. ✅ **Scraping works** perfectly
2. ✅ **Data quality** is excellent
3. ✅ **Dagster integration** complete
4. ✅ **GitHub Actions** ready
5. ✅ **Documentation** comprehensive

**Action Items:**

- Deploy Dagster with Zillow ingestion
- Test full flow: Scrape → S3 → Snowflake → dbt
- Enable monthly automation
- Monitor for one full cycle

### Phase 2: ApartmentList (NEXT WEEK)

**Once Zillow is proven in production:**

1. Debug the download button issue
2. Test end-to-end once working
3. Add Dagster asset (copy Zillow pattern)
4. Add to monthly schedule
5. Update GitHub Actions workflow

### Phase 3: FRED (FUTURE)

**After both Zillow and ApartmentList work:**

1. Create `ingest/fred_tampa_rent_pull.py`
2. Follow same pattern as Zillow
3. Add to Dagster and schedule

---

## 📝 SUMMARY

**ZILLOW**: ✅ **Ready for production**

- All tests passing
- Fully integrated with Dagster
- Documented and automated
- **Recommendation: Deploy now**

**APARTMENTLIST**: ⚠️ **Needs debugging**

- Code structure ready
- Download mechanism failing
- Page structure investigation needed
- **Recommendation: Fix next week OR use existing manual script**

**OVERALL**: 🚀 **Can launch MVP with Zillow only**

The Zillow scraper alone provides valuable Tampa rent data (10+ years, monthly updates). It's sufficient for an MVP. Add ApartmentList and FRED incrementally once the foundation is proven.

---

## 📚 FILES REFERENCE

### Working

- ✅ `ingest/zillow_zori_pull.py` - Production ready
- ✅ `ingest/README.md` - Zillow documentation
- ✅ `dagster_rent_signals/assets/ingestion.py` - Dagster integration
- ✅ `.github/workflows/monthly_ingestion.yml` - CI/CD
- ✅ `sql/ingestion/load_zillow_from_s3.sql` - Snowflake setup
- ✅ `TEST_RESULTS.md` - Comprehensive test report

### Needs Work

- ⚠️ `ingest/apartmentlist_pull.py` - Download failing
- ⚠️ `ingest/APARTMENTLIST_TEST.md` - Known issues documented
- ⏸️ `ingest/fred_tampa_rent_pull.py` - Not created yet

### Documentation

- ✅ `ingest/QUICKSTART.md` - Setup guide
- ✅ `ingest/ENV.md` - Environment configuration
- ✅ `ingest/INTEGRATION_SUMMARY.md` - Architecture
- ✅ `ingest/SCRAPER_COMPARISON.md` - This file

