# Environment Configuration for Ingestion Pipeline

This document describes the environment variables and configuration needed to run the automated ingestion pipeline with Dagster and GitHub Actions.

## Local Development (Dagster)

### Required Environment Variables

```bash
# AWS Configuration (for S3 uploads)
export AWS_PROFILE=default                    # AWS CLI profile name
export AWS_REGION=us-east-1                   # AWS region for S3 bucket
export BUCKET=rent-signals-dev-<initials>     # S3 bucket name (must match your bucket)

# Snowflake Configuration (for dbt downstream)
export SNOWFLAKE_ACCOUNT="<account_id>"
export SNOWFLAKE_USER="<username>"
export SNOWFLAKE_PASSWORD="<password>"
export SNOWFLAKE_DATABASE="RENTS"
export SNOWFLAKE_WAREHOUSE="WH_XS"
export SNOWFLAKE_ROLE="ACCOUNTADMIN"
export SNOWFLAKE_SCHEMA="DBT_DEV"
```

### Running Dagster Locally

1. **Install Dagster dependencies:**

   ```bash
   cd dagster_rent_signals
   pip install -e ".[dev]"
   ```

2. **Set environment variables:**

   ```bash
   # Copy and edit your environment file
   source .env  # or manually export variables
   ```

3. **Start Dagster UI:**

   ```bash
   dagster dev
   ```

4. **Access the UI:**
   - Open http://localhost:3000
   - Navigate to Assets → ingestion
   - Materialize `zillow_zori_ingestion` asset
   - Check run logs and S3 uploads

### Testing the Ingestion Locally

```bash
# Test the Zillow script directly
cd /path/to/tampa-rent-signals
python ingest/zillow_zori_pull.py

# Verify output
ls -R data/bronze/zillow_zori/
ls -R data/silver/zillow_zori/

# Test S3 upload manually
aws s3 ls s3://${BUCKET}/zillow/bronze/ --recursive
aws s3 ls s3://${BUCKET}/zillow/silver/ --recursive
```

## GitHub Actions (CI/CD)

### Required GitHub Secrets

Configure these in your GitHub repository: **Settings → Secrets and variables → Actions**

| Secret Name    | Description                             | Example                                                 |
| -------------- | --------------------------------------- | ------------------------------------------------------- |
| `AWS_ROLE_ARN` | ARN of IAM role for OIDC authentication | `arn:aws:iam::123456789:role/RentSignalsGhOidcUploader` |
| `S3_BUCKET`    | S3 bucket name for data storage         | `rent-signals-dev-dd`                                   |

### Setting Up AWS OIDC Authentication

GitHub Actions uses OpenID Connect (OIDC) for keyless AWS authentication. This is more secure than storing AWS access keys.

#### 1. Create GitHub OIDC Provider in AWS

```bash
# This only needs to be done once per AWS account
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

#### 2. Create IAM Role with Trust Policy

Edit `infra/aws/policies/gh-oidc-trust.json` (use the TEMPLATE):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/tampa-rent-signals:*"
        }
      }
    }
  ]
}
```

Replace:

- `YOUR_ACCOUNT_ID` with your AWS account ID
- `YOUR_GITHUB_ORG` with your GitHub username or organization
- `tampa-rent-signals` with your repository name

#### 3. Create the IAM Role

```bash
# Create role
aws iam create-role \
  --role-name RentSignalsGhOidcUploader \
  --assume-role-policy-document file://infra/aws/policies/gh-oidc-trust.json

# Attach S3 upload policy
aws iam put-role-policy \
  --role-name RentSignalsGhOidcUploader \
  --policy-name S3UploadPolicy \
  --policy-document file://infra/aws/policies/gh-oidc-s3-uploader.json

# Get the role ARN (save this for GitHub secrets)
aws iam get-role --role-name RentSignalsGhOidcUploader --query 'Role.Arn' --output text
```

#### 4. Add Secrets to GitHub

1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add `AWS_ROLE_ARN` with the ARN from step 3
5. Add `S3_BUCKET` with your bucket name

### Manual Workflow Trigger

You can manually trigger the ingestion workflow:

1. Go to **Actions** tab in GitHub
2. Select **Monthly Data Ingestion** workflow
3. Click **Run workflow**
4. Optional: Check "Force re-download" to override idempotency
5. Click **Run workflow** button

### Workflow Schedule

The workflow runs automatically:

- **Schedule**: 2nd day of every month at 4 AM UTC (11 PM EST previous day)
- **Reason**: Data typically updates on the 1st, so we run on the 2nd to ensure availability

## Production Deployment (Dagster Cloud)

### Option 1: Dagster Cloud

If using Dagster Cloud (dagster.cloud):

1. **Set up Dagster Cloud account**
2. **Deploy project:**

   ```bash
   dagster-cloud deployment create
   ```

3. **Configure environment variables** in Dagster Cloud UI:

   - AWS_PROFILE (if using profile)
   - AWS_REGION
   - BUCKET
   - SNOWFLAKE\_\* variables

4. **Enable schedules** in Dagster Cloud UI

### Option 2: Self-Hosted Dagster

If self-hosting on EC2/ECS/K8s:

1. **Install Dagster daemon:**

   ```bash
   pip install dagster dagster-webserver dagster-daemon
   ```

2. **Create systemd service** or Docker container
3. **Set environment variables** in service configuration
4. **Start daemon:**
   ```bash
   dagster-daemon run
   ```

## Troubleshooting

### Dagster: Asset fails with "S3 bucket not found"

**Solution**: Ensure the `BUCKET` environment variable is set and matches your S3 bucket name.

```bash
# Verify bucket exists
aws s3 ls s3://${BUCKET}/

# Check environment variable
echo $BUCKET
```

### Dagster: "zillow_zori_pull.py not found"

**Solution**: The asset looks for the script relative to project root. Ensure you're running Dagster from the correct directory.

```bash
# Should be in dagster_rent_signals/ directory
cd dagster_rent_signals
dagster dev
```

### GitHub Actions: "Access Denied" on S3 upload

**Solution**: Check IAM role permissions and trust policy.

```bash
# Verify role policy
aws iam get-role-policy \
  --role-name RentSignalsGhOidcUploader \
  --policy-name S3UploadPolicy

# Check trust policy
aws iam get-role \
  --role-name RentSignalsGhOidcUploader \
  --query 'Role.AssumeRolePolicyDocument'
```

### GitHub Actions: "No such file or directory: data/bronze"

**Solution**: The ingestion script hasn't created output yet. Check script logs for errors.

```bash
# Test locally first
python ingest/zillow_zori_pull.py

# Check if data was created
ls -R data/
```

### Local Development: ImportError for dagster modules

**Solution**: Install Dagster project in editable mode.

```bash
cd dagster_rent_signals
pip install -e ".[dev]"
```

## Monitoring and Alerting

### Dagster UI Monitoring

- **Asset Status**: Check green/red status indicators
- **Run History**: View past materializations and failures
- **Logs**: Detailed execution logs with S3 upload confirmations
- **Metadata**: Row counts, file sizes, S3 URIs

### GitHub Actions Monitoring

- **Workflow Status**: Green checkmark or red X on Actions tab
- **Email Notifications**: GitHub sends emails on workflow failures
- **Artifacts**: Download ingestion output for debugging

### S3 Monitoring

```bash
# Check latest uploads
aws s3 ls s3://${BUCKET}/zillow/ --recursive | tail -20

# Verify partitioned structure
aws s3 ls s3://${BUCKET}/zillow/bronze/
aws s3 ls s3://${BUCKET}/zillow/silver/

# Check file sizes
aws s3 ls s3://${BUCKET}/zillow/ --recursive --human-readable --summarize
```

## Next Steps

Once ingestion is working:

1. **Configure Snowflake external stage** to read from S3
2. **Create Snowflake tasks** to load from S3 to raw tables
3. **Run dbt models** to transform raw → staging → core → marts
4. **Set up data quality checks** with Great Expectations
5. **Create dashboards** or API endpoints for consumption

## Support

For issues or questions:

- Check Dagster logs in UI (http://localhost:3000)
- Review GitHub Actions workflow logs
- Inspect S3 bucket contents with AWS CLI
- Verify environment variables are set correctly

