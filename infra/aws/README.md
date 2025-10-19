# AWS Infrastructure Setup for Rent Signals Pipeline

This directory contains AWS infrastructure setup for a Snowflake-connected data pipeline with GitHub Actions CI/CD.

## Prerequisites

- AWS CLI installed and configured
- Active AWS account (ID: 607709788146)
- Proper AWS credentials in `~/.aws/credentials`
- Git repository initialized

## Required Environment Variables

Export these variables before running any commands:

```bash
export AWS_PROFILE=default
export AWS_REGION=us-east-1
export BUCKET=rent-signals-dev-<initials-or-random>   # must be globally unique
export TODAY=$(date +%F)
```

## Quick Setup

From the repository root, run:

```bash
make create-bucket create-prefixes upload-samples verify
```

## Step-by-Step Setup

### 1. S3 Bucket Setup

Create the bucket with security best practices:

```bash
make create-bucket
```

This will:
- Create the S3 bucket (handles us-east-1 special case)
- Block all public access
- Enable SSE-S3 default encryption (AES256)
- Enable versioning

### 2. Create Data Prefixes

```bash
make create-prefixes
```

Creates directory structure:
- `zillow/$TODAY/`
- `aptlist/$TODAY/`
- `fred/$TODAY/`

### 3. Upload Sample Data

```bash
make upload-samples
```

Uploads standardized CSV files:
- `standardized/zori_zip_long.csv` → `s3://$BUCKET/zillow/$TODAY/`
- `standardized/apartmentlist_long.csv` → `s3://$BUCKET/aptlist/$TODAY/`
- `standardized/fred_cpi_long.csv` → `s3://$BUCKET/fred/$TODAY/`

### 4. Create IAM Policy for Snowflake

```bash
make create-readonly-policy
```

This creates the `RentSignalsS3ReadOnly` policy and prints its ARN. **Copy this ARN** - you'll need it when creating the Snowflake role.

### 5. Snowflake Integration Setup

#### 5.1 Create Storage Integration in Snowflake

In Snowflake, run:

```sql
CREATE STORAGE INTEGRATION s3_int
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::607709788146:role/SnowflakeS3ExternalStage'
  STORAGE_ALLOWED_LOCATIONS = ('s3://YOUR_BUCKET_NAME/');
```

#### 5.2 Get Snowflake IAM Details

```sql
DESC STORAGE INTEGRATION s3_int;
```

Copy the values for:
- `STORAGE_AWS_IAM_USER_ARN`
- `STORAGE_AWS_EXTERNAL_ID`

#### 5.3 Fill Trust Template

1. Copy the trust template:
   ```bash
   cp infra/aws/policies/trust-snowflake.json.TEMPLATE infra/aws/policies/trust-snowflake.json
   ```

2. Replace placeholders in `trust-snowflake.json`:
   - `REPLACE_WITH_STORAGE_AWS_IAM_USER_ARN` → value from step 5.2
   - `REPLACE_WITH_STORAGE_AWS_EXTERNAL_ID` → value from step 5.2

#### 5.4 Create Snowflake Role

```bash
aws iam create-role \
  --role-name SnowflakeS3ExternalStage \
  --assume-role-policy-document file://infra/aws/policies/trust-snowflake.json \
  --profile "$AWS_PROFILE"

aws iam attach-role-policy \
  --role-name SnowflakeS3ExternalStage \
  --policy-arn arn:aws:iam::607709788146:policy/RentSignalsS3ReadOnly \
  --profile "$AWS_PROFILE"
```

### 6. GitHub OIDC Setup (Optional)

For CI/CD uploads without static AWS keys:

#### 6.1 Create GitHub OIDC Provider (One-time setup)

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --profile "$AWS_PROFILE"
```

#### 6.2 Fill GitHub Trust Template

1. Copy the template:
   ```bash
   cp infra/aws/policies/gh-oidc-trust.json.TEMPLATE infra/aws/policies/gh-oidc-trust.json
   ```

2. Replace placeholders:
   - `<OWNER>` → your GitHub username (e.g., `DrakeDamon`)
   - `<REPO>` → your repository name (e.g., `rental_signals`)
   - Optionally change `main` if your default branch differs

#### 6.3 Create GitHub OIDC Role

```bash
make create-oidc-role
```

### 7. Verification

Check all configurations:

```bash
make verify
```

## GitHub Actions Integration

Sample workflow (`.github/workflows/upload-data.yml`):

```yaml
name: Upload Data to S3

on:
  push:
    branches: [main]
    paths: ['standardized/**']

jobs:
  upload:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::607709788146:role/RentSignalsGhOidcUploader
          aws-region: us-east-1
          
      - name: Upload to S3
        env:
          BUCKET: rent-signals-dev-dd
          TODAY: ${{ github.event.head_commit.timestamp }}
        run: |
          TODAY=$(date +%F)
          aws s3 cp standardized/zori_zip_long.csv "s3://$BUCKET/zillow/$TODAY/"
          aws s3 cp standardized/apartmentlist_long.csv "s3://$BUCKET/aptlist/$TODAY/"
          aws s3 cp standardized/fred_cpi_long.csv "s3://$BUCKET/fred/$TODAY/"
```

## Security Features

- ✅ No static AWS keys in repository
- ✅ S3 bucket with blocked public access
- ✅ SSE-S3 encryption enabled
- ✅ Least-privilege IAM policies
- ✅ Scoped to specific S3 prefixes only
- ✅ OIDC-based CI authentication

## File Structure

```
infra/aws/
├── policies/
│   ├── s3-readonly-rentsignals.json           # Snowflake read-only policy
│   ├── trust-snowflake.json.TEMPLATE          # Snowflake trust template
│   ├── gh-oidc-trust.json.TEMPLATE           # GitHub OIDC trust template
│   └── gh-oidc-s3-uploader.json              # GitHub OIDC uploader policy
└── README.md                                   # This file
```

## Troubleshooting

### Bucket Creation Fails
- Ensure bucket name is globally unique
- Check AWS credentials and permissions

### us-east-1 Create Bucket Error
The Makefile handles this automatically, but if running commands manually:
- For us-east-1: omit `--create-bucket-configuration`
- For other regions: include `--create-bucket-configuration LocationConstraint=REGION`

### Policy ARN Not Found
After creating the policy, wait a few seconds for AWS to propagate the changes.

### Snowflake Integration Fails
- Verify the role ARN in the storage integration matches exactly
- Ensure trust policy has correct IAM user ARN and external ID
- Check that the policy is attached to the role

## Available Make Targets

- `make help` - Show help and required environment variables
- `make create-bucket` - Create S3 bucket with security settings
- `make create-prefixes` - Create data prefixes
- `make upload-samples` - Upload standardized CSVs
- `make create-readonly-policy` - Create IAM policy (prints ARN)
- `make create-oidc-role` - Create GitHub OIDC role
- `make verify` - Verify all configurations