.PHONY: create-bucket create-prefixes upload-samples create-readonly-policy create-oidc-role verify help
.DEFAULT_GOAL := help

# Ensure required environment variables are set
check-env:
	@if [ -z "$$BUCKET" ]; then echo "Error: BUCKET env var not set"; exit 1; fi
	@if [ -z "$$AWS_REGION" ]; then echo "Error: AWS_REGION env var not set"; exit 1; fi
	@if [ -z "$$TODAY" ]; then echo "Error: TODAY env var not set"; exit 1; fi
	@if [ -z "$$AWS_PROFILE" ]; then echo "Error: AWS_PROFILE env var not set"; exit 1; fi

help:
	@echo "AWS S3 + IAM Setup for Rent Signals Pipeline"
	@echo ""
	@echo "Required environment variables:"
	@echo "  export AWS_PROFILE=default"
	@echo "  export AWS_REGION=us-east-1"
	@echo "  export BUCKET=rent-signals-dev-<initials-or-random>"
	@echo "  export TODAY=\$$(date +%F)"
	@echo ""
	@echo "Available targets:"
	@echo "  create-bucket       Create S3 bucket with security settings"
	@echo "  create-prefixes     Create data prefixes (zillow/, aptlist/, fred/)"
	@echo "  upload-samples      Upload standardized CSVs to today's prefixes"
	@echo "  create-readonly-policy  Create IAM policy for Snowflake (prints ARN)"
	@echo "  create-oidc-role    Create GitHub OIDC role for CI uploads"
	@echo "  verify             Verify bucket configuration and uploads"
	@echo ""
	@echo "Quick setup:"
	@echo "  make create-bucket create-prefixes upload-samples verify"

create-bucket: check-env
	@echo "Creating S3 bucket: $$BUCKET in region: $$AWS_REGION"
	@set -euo pipefail; \
	if [ "$$AWS_REGION" = "us-east-1" ]; then \
		aws s3api create-bucket --bucket "$$BUCKET" --profile "$$AWS_PROFILE"; \
	else \
		aws s3api create-bucket --bucket "$$BUCKET" --region "$$AWS_REGION" \
			--create-bucket-configuration LocationConstraint="$$AWS_REGION" --profile "$$AWS_PROFILE"; \
	fi
	@echo "Blocking public access..."
	aws s3api put-public-access-block --bucket "$$BUCKET" --profile "$$AWS_PROFILE" \
		--public-access-block-configuration \
		"BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
	@echo "Enabling default encryption..."
	aws s3api put-bucket-encryption --bucket "$$BUCKET" --profile "$$AWS_PROFILE" \
		--server-side-encryption-configuration \
		'{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
	@echo "Enabling versioning..."
	aws s3api put-bucket-versioning --bucket "$$BUCKET" --profile "$$AWS_PROFILE" \
		--versioning-configuration Status=Enabled
	@echo "✅ Bucket $$BUCKET created successfully"

create-prefixes: check-env
	@echo "Creating data prefixes for date: $$TODAY"
	@set -euo pipefail; \
	for prefix in zillow aptlist fred; do \
		echo "Creating prefix: $$prefix/$$TODAY/"; \
		aws s3api put-object --bucket "$$BUCKET" --key "$$prefix/$$TODAY/" --profile "$$AWS_PROFILE"; \
	done
	@echo "✅ Prefixes created successfully"

upload-samples: check-env
	@echo "Uploading standardized CSV files to $$TODAY prefixes..."
	@set -euo pipefail; \
	if [ ! -f "standardized/zori_zip_long.csv" ]; then echo "Error: standardized/zori_zip_long.csv not found"; exit 1; fi; \
	if [ ! -f "standardized/apartmentlist_long.csv" ]; then echo "Error: standardized/apartmentlist_long.csv not found"; exit 1; fi; \
	if [ ! -f "standardized/fred_cpi_long.csv" ]; then echo "Error: standardized/fred_cpi_long.csv not found"; exit 1; fi
	@echo "Uploading Zillow data..."
	aws s3 cp standardized/zori_zip_long.csv "s3://$$BUCKET/zillow/$$TODAY/" --profile "$$AWS_PROFILE"
	@echo "Uploading ApartmentList data..."
	aws s3 cp standardized/apartmentlist_long.csv "s3://$$BUCKET/aptlist/$$TODAY/" --profile "$$AWS_PROFILE"
	@echo "Uploading FRED data..."
	aws s3 cp standardized/fred_cpi_long.csv "s3://$$BUCKET/fred/$$TODAY/" --profile "$$AWS_PROFILE"
	@echo "✅ Sample files uploaded successfully"

create-readonly-policy: check-env
	@echo "Creating S3 read-only policy for Snowflake..."
	@set -euo pipefail; \
	sed "s/\$${BUCKET}/$$BUCKET/g" infra/aws/policies/s3-readonly-rentsignals.json > /tmp/s3-readonly-rentsignals.json
	@aws iam create-policy \
		--policy-name RentSignalsS3ReadOnly \
		--policy-document file:///tmp/s3-readonly-rentsignals.json \
		--profile "$$AWS_PROFILE" | jq -r '.Policy.Arn'
	@echo ""
	@echo "✅ Policy created. Copy the ARN above for attaching to Snowflake role later."
	@rm /tmp/s3-readonly-rentsignals.json

create-oidc-role: check-env
	@echo "Creating GitHub OIDC role for CI uploads..."
	@echo "⚠️  First, ensure you've filled in <OWNER> and <REPO> in infra/aws/policies/gh-oidc-trust.json.TEMPLATE"
	@echo "⚠️  and saved it as gh-oidc-trust.json"
	@if [ ! -f "infra/aws/policies/gh-oidc-trust.json" ]; then \
		echo "Error: infra/aws/policies/gh-oidc-trust.json not found"; \
		echo "Please copy gh-oidc-trust.json.TEMPLATE to gh-oidc-trust.json and fill in placeholders"; \
		exit 1; \
	fi
	@set -euo pipefail; \
	sed "s/\$${BUCKET}/$$BUCKET/g" infra/aws/policies/gh-oidc-s3-uploader.json > /tmp/gh-oidc-s3-uploader.json
	@echo "Creating role..."
	aws iam create-role \
		--role-name RentSignalsGhOidcUploader \
		--assume-role-policy-document file://infra/aws/policies/gh-oidc-trust.json \
		--profile "$$AWS_PROFILE"
	@echo "Attaching inline policy..."
	aws iam put-role-policy \
		--role-name RentSignalsGhOidcUploader \
		--policy-name RentSignalsGhOidcS3UploaderInline \
		--policy-document file:///tmp/gh-oidc-s3-uploader.json \
		--profile "$$AWS_PROFILE"
	@echo "✅ GitHub OIDC role created successfully"
	@rm /tmp/gh-oidc-s3-uploader.json

verify: check-env
	@echo "Verifying S3 bucket configuration..."
	@echo ""
	@echo "🔒 Public Access Block:"
	aws s3api get-public-access-block --bucket "$$BUCKET" --profile "$$AWS_PROFILE"
	@echo ""
	@echo "🔐 Bucket Encryption:"
	aws s3api get-bucket-encryption --bucket "$$BUCKET" --profile "$$AWS_PROFILE"
	@echo ""
	@echo "📁 Prefix Contents:"
	@echo "Zillow prefix:"
	aws s3 ls "s3://$$BUCKET/zillow/$$TODAY/" --profile "$$AWS_PROFILE"
	@echo "ApartmentList prefix:"
	aws s3 ls "s3://$$BUCKET/aptlist/$$TODAY/" --profile "$$AWS_PROFILE"
	@echo "FRED prefix:"
	aws s3 ls "s3://$$BUCKET/fred/$$TODAY/" --profile "$$AWS_PROFILE"
	@echo ""
	@echo "🔑 IAM Policy Check:"
	@aws iam get-policy --policy-arn "arn:aws:iam::607709788146:policy/RentSignalsS3ReadOnly" --profile "$$AWS_PROFILE" >/dev/null 2>&1 \
		&& echo "✅ RentSignalsS3ReadOnly policy exists" \
		|| echo "❌ RentSignalsS3ReadOnly policy not found"
	@echo ""
	@echo "🤖 IAM Role Check:"
	@aws iam get-role --role-name SnowflakeS3ExternalStage --profile "$$AWS_PROFILE" >/dev/null 2>&1 \
		&& echo "✅ SnowflakeS3ExternalStage role exists" \
		|| echo "❌ SnowflakeS3ExternalStage role not found (create after Snowflake setup)"
	@aws iam get-role --role-name RentSignalsGhOidcUploader --profile "$$AWS_PROFILE" >/dev/null 2>&1 \
		&& echo "✅ RentSignalsGhOidcUploader role exists" \
		|| echo "❌ RentSignalsGhOidcUploader role not found (optional)"