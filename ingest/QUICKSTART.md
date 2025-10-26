# Zillow Ingestion - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will help you set up and run the Zillow ZORI ingestion pipeline using Dagster.

## Prerequisites

- Python 3.8+
- AWS CLI configured
- S3 bucket created (see main README.md)
- Dagster installed

## Option 1: Run with Dagster (Recommended)

### Step 1: Install Dependencies

```bash
cd dagster_rent_signals
pip install -e ".[dev]"
```

### Step 2: Set Environment Variables

```bash
export AWS_PROFILE=default
export AWS_REGION=us-east-1
export BUCKET=rent-signals-dev-yourname   # Your S3 bucket name
```

### Step 3: Start Dagster

```bash
dagster dev
```

### Step 4: Materialize Asset

1. Open http://localhost:3000
2. Go to **Assets** → **ingestion** group
3. Click on `zillow_zori_ingestion`
4. Click **Materialize** button
5. Watch the logs for progress

### What Happens:

1. ✅ Downloads latest Zillow ZORI data
2. ✅ Creates bronze layer (raw CSV): `data/bronze/zillow_zori/date=YYYY-MM/`
3. ✅ Creates silver layer (Tampa Parquet): `data/silver/zillow_zori/date=YYYY-MM/`
4. ✅ Uploads both to S3: `s3://{bucket}/zillow/bronze/` and `s3://{bucket}/zillow/silver/`
5. ✅ Shows metadata: row count, file sizes, S3 URIs

## Option 2: Run Script Directly (Manual)

### Step 1: Run Ingestion Script

```bash
cd /path/to/tampa-rent-signals
python ingest/zillow_zori_pull.py
```

### Step 2: Verify Output

```bash
# Check local files
ls -R data/bronze/zillow_zori/
ls -R data/silver/zillow_zori/
```

### Step 3: Upload to S3 Manually

```bash
# Set variables
export BUCKET=rent-signals-dev-yourname
LATEST_DATE=$(ls -1 data/silver/zillow_zori/ | grep '^date=' | sort -r | head -1 | cut -d'=' -f2)

# Upload bronze
aws s3 sync \
  data/bronze/zillow_zori/date=${LATEST_DATE}/ \
  s3://${BUCKET}/zillow/bronze/date=${LATEST_DATE}/

# Upload silver
aws s3 sync \
  data/silver/zillow_zori/date=${LATEST_DATE}/ \
  s3://${BUCKET}/zillow/silver/date=${LATEST_DATE}/

# Verify
aws s3 ls s3://${BUCKET}/zillow/ --recursive
```

## Option 3: Automated Monthly Runs (GitHub Actions)

### Step 1: Configure GitHub Secrets

Go to your repo: **Settings → Secrets → Actions**

Add these secrets:

- `AWS_ROLE_ARN`: Your IAM role ARN for OIDC
- `S3_BUCKET`: Your S3 bucket name

See `ingest/ENV.md` for detailed OIDC setup instructions.

### Step 2: Enable Workflow

The workflow `.github/workflows/monthly_ingestion.yml` is already set up!

It runs automatically:

- **Schedule**: 2nd day of each month at 4 AM UTC
- **Manual**: Actions tab → Monthly Data Ingestion → Run workflow

### Step 3: Monitor Execution

1. Go to **Actions** tab in GitHub
2. Click on the latest workflow run
3. View logs and download artifacts

## Verify Everything Works

### Check Local Files

```bash
# Bronze layer (raw CSV)
ls -lh data/bronze/zillow_zori/date=*/

# Silver layer (Tampa Parquet)
ls -lh data/silver/zillow_zori/date=*/

# Inspect parquet
python -c "
import pyarrow.parquet as pq
df = pq.read_table('data/silver/zillow_zori/date=2025-09/zori_tampa.parquet').to_pandas()
print(f'Rows: {len(df)}')
print(df.head())
"
```

### Check S3 Uploads

```bash
export BUCKET=rent-signals-dev-yourname

# List all Zillow data
aws s3 ls s3://${BUCKET}/zillow/ --recursive --human-readable

# Check latest bronze
aws s3 ls s3://${BUCKET}/zillow/bronze/ --recursive | tail -5

# Check latest silver
aws s3 ls s3://${BUCKET}/zillow/silver/ --recursive | tail -5
```

### Check Dagster UI

1. Open http://localhost:3000
2. Go to **Assets** → `zillow_zori_ingestion`
3. Click on latest materialization
4. Check **Metadata** tab for:
   - Ingested month
   - Row count
   - Bronze/Silver S3 paths
   - Upload confirmations

## Troubleshooting

### Problem: "No module named 'dagster'"

**Solution:**

```bash
cd dagster_rent_signals
pip install -e ".[dev]"
```

### Problem: "BUCKET environment variable not set"

**Solution:**

```bash
export BUCKET=your-bucket-name
```

### Problem: "Access Denied" when uploading to S3

**Solution:**

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check bucket access
aws s3 ls s3://${BUCKET}/
```

### Problem: "zillow_zori_pull.py not found"

**Solution:**
Make sure you're running from the project root or Dagster is in the `dagster_rent_signals/` directory.

### Problem: Script says "No new ZORI data to ingest"

**Solution:**
The script is idempotent - it won't re-download data for months that already exist. Use `--force` to override:

```bash
python ingest/zillow_zori_pull.py --force
```

## Next Steps

Once ingestion is working:

1. **Set up Snowflake integration:**

   - Create external stage pointing to S3
   - Load data from S3 to Snowflake raw tables

2. **Run dbt pipeline:**

   ```bash
   cd dbt_rent_signals
   dbt run --models staging
   dbt run --models core
   dbt run --models marts
   ```

3. **Add more data sources:**

   - ApartmentList: `ingest/apartmentlist_pull.py` (coming soon)
   - FRED: `ingest/fred_tampa_rent_pull.py` (coming soon)

4. **Set up monitoring:**
   - Dagster sensors for data freshness
   - Great Expectations for data quality
   - Alerts for pipeline failures

## Schedule Configuration

### Dagster Schedule (Local/Cloud)

The schedule is already configured:

- **Frequency**: Monthly on the 2nd at 3 AM EST
- **Timezone**: America/New_York
- **Status**: Running (auto-enabled)

To disable in Dagster UI:

1. Go to **Schedules**
2. Find `monthly_ingestion_schedule`
3. Click **Stop Schedule**

### GitHub Actions Schedule

Edit `.github/workflows/monthly_ingestion.yml`:

```yaml
schedule:
  - cron: "0 4 2 * *" # 2nd day of month at 4 AM UTC
```

## Support

- **Documentation**: See `ingest/ENV.md` for detailed configuration
- **Dagster Docs**: https://docs.dagster.io
- **Script Details**: See `ingest/README.md` for Zillow script specifics

## Success Checklist

- [ ] Dagster UI starts successfully
- [ ] Environment variables set (BUCKET, AWS_PROFILE, AWS_REGION)
- [ ] `zillow_zori_ingestion` asset materializes without errors
- [ ] Local files created in `data/bronze/` and `data/silver/`
- [ ] Files uploaded to S3 successfully
- [ ] Dagster metadata shows row counts and S3 paths
- [ ] Schedule appears in Dagster UI
- [ ] GitHub Actions secrets configured (if using CI/CD)

Once all items are checked, your ingestion pipeline is ready for production! 🎉

