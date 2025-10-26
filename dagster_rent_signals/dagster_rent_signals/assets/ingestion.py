"""Data ingestion assets for Tampa Rent Signals pipeline.

These assets run data collection scripts, save to local bronze/silver layers,
and upload to S3 for Snowflake ingestion.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dagster import (
    asset,
    AssetExecutionContext,
    Output,
    MetadataValue,
    FreshnessPolicy,
)

from ..resources.s3 import S3Resource

# Project root directory
PROJECT_ROOT = Path(__file__).parents[4]  # Up to tampa-rent-signals/
INGEST_DIR = PROJECT_ROOT / "ingest"


@asset(
    group_name="ingestion",
    description="Download and process Zillow ZORI data for Tampa metro area",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 24 * 32),  # ~1 month
    metadata={
        "source": "Zillow ZORI",
        "update_frequency": "monthly",
        "layer": "bronze_silver",
    },
)
def zillow_zori_ingestion(
    context: AssetExecutionContext,
    s3: S3Resource,
) -> Output[dict[str, Any]]:
    """
    Run Zillow ZORI ingestion script and upload outputs to S3.
    
    This asset:
    1. Executes ingest/zillow_zori_pull.py to download latest ZORI data
    2. Transforms to bronze (raw CSV) and silver (Tampa Parquet) layers
    3. Uploads both layers to S3 with date partitioning
    4. Returns metadata about the ingestion run
    
    Bronze: data/bronze/zillow_zori/date=YYYY-MM/*.csv
    Silver: data/silver/zillow_zori/date=YYYY-MM/*.parquet
    
    S3 Structure: zillow/bronze/date=YYYY-MM/ and zillow/silver/date=YYYY-MM/
    """
    script_path = INGEST_DIR / "zillow_zori_pull.py"
    
    if not script_path.exists():
        raise FileNotFoundError(f"Zillow ingestion script not found: {script_path}")
    
    context.log.info(f"Running Zillow ZORI ingestion script: {script_path}")
    
    # Run the ingestion script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        context.log.error(f"Script failed with exit code {result.returncode}")
        context.log.error(f"STDOUT: {result.stdout}")
        context.log.error(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Zillow ingestion script failed: {result.stderr}")
    
    context.log.info(f"Script output: {result.stdout}")
    
    # Parse output to find what was ingested
    # Expected format: "zillow_zori: latest=2025-09 rows=129 saved=data/silver/..."
    ingested_month = None
    row_count = 0
    
    for line in result.stdout.splitlines():
        if "latest=" in line and "rows=" in line:
            parts = line.split()
            for part in parts:
                if part.startswith("latest="):
                    ingested_month = part.split("=")[1]
                elif part.startswith("rows="):
                    row_count = int(part.split("=")[1])
    
    if not ingested_month:
        # Try to infer from directory structure
        silver_base = PROJECT_ROOT / "data" / "silver" / "zillow_zori"
        if silver_base.exists():
            date_dirs = sorted([d.name.replace("date=", "") 
                              for d in silver_base.glob("date=*") if d.is_dir()])
            if date_dirs:
                ingested_month = date_dirs[-1]
    
    if not ingested_month:
        raise RuntimeError("Could not determine ingested month from script output")
    
    context.log.info(f"Ingested month: {ingested_month}, rows: {row_count}")
    
    # Upload bronze layer to S3
    bronze_dir = PROJECT_ROOT / "data" / "bronze" / "zillow_zori" / f"date={ingested_month}"
    bronze_uris = []
    
    if bronze_dir.exists():
        context.log.info(f"Uploading bronze layer from {bronze_dir}")
        for csv_file in bronze_dir.glob("*.csv"):
            uri = s3.upload_partitioned_data(
                source="zillow",
                layer="bronze",
                date=ingested_month,
                local_path=csv_file
            )
            bronze_uris.append(uri)
            context.log.info(f"Uploaded bronze: {uri}")
    else:
        context.log.warning(f"Bronze directory not found: {bronze_dir}")
    
    # Upload silver layer to S3
    silver_dir = PROJECT_ROOT / "data" / "silver" / "zillow_zori" / f"date={ingested_month}"
    silver_uris = []
    
    if silver_dir.exists():
        context.log.info(f"Uploading silver layer from {silver_dir}")
        for parquet_file in silver_dir.glob("*.parquet"):
            uri = s3.upload_partitioned_data(
                source="zillow",
                layer="silver",
                date=ingested_month,
                local_path=parquet_file
            )
            silver_uris.append(uri)
            context.log.info(f"Uploaded silver: {uri}")
    else:
        context.log.warning(f"Silver directory not found: {silver_dir}")
    
    metadata = {
        "ingested_month": MetadataValue.text(ingested_month),
        "row_count": MetadataValue.int(row_count),
        "bronze_files_uploaded": MetadataValue.int(len(bronze_uris)),
        "silver_files_uploaded": MetadataValue.int(len(silver_uris)),
        "bronze_s3_paths": MetadataValue.md("\n".join(f"- `{uri}`" for uri in bronze_uris)),
        "silver_s3_paths": MetadataValue.md("\n".join(f"- `{uri}`" for uri in silver_uris)),
        "run_timestamp": MetadataValue.timestamp(datetime.now().timestamp()),
    }
    
    return Output(
        value={
            "month": ingested_month,
            "rows": row_count,
            "bronze_uris": bronze_uris,
            "silver_uris": silver_uris,
        },
        metadata=metadata,
    )


@asset(
    group_name="ingestion",
    description="Download and process ApartmentList rent estimates for Tampa metro area",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 24 * 32),  # ~1 month
    metadata={
        "source": "ApartmentList",
        "update_frequency": "monthly",
        "layer": "bronze_silver",
    },
)
def apartmentlist_ingestion(
    context: AssetExecutionContext,
    s3: S3Resource,
) -> Output[dict[str, Any]]:
    """
    Run ApartmentList ingestion script and upload outputs to S3.
    
    This asset:
    1. Executes ingest/apartmentlist_pull.py to download latest rent estimates
    2. Transforms to bronze (raw CSV) and silver (Tampa Parquet) layers
    3. Uploads both layers to S3 with date partitioning
    4. Returns metadata about the ingestion run
    
    Bronze: data/bronze/apartmentlist/date=YYYY-MM/*.csv
    Silver: data/silver/apartmentlist/date=YYYY-MM/*.parquet
    
    S3 Structure: apartmentlist/bronze/date=YYYY-MM/ and apartmentlist/silver/date=YYYY-MM/
    """
    script_path = INGEST_DIR / "apartmentlist_pull.py"
    
    if not script_path.exists():
        raise FileNotFoundError(f"ApartmentList ingestion script not found: {script_path}")
    
    context.log.info(f"Running ApartmentList ingestion script: {script_path}")
    
    # Run the ingestion script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        context.log.error(f"Script failed with exit code {result.returncode}")
        context.log.error(f"STDOUT: {result.stdout}")
        context.log.error(f"STDERR: {result.stderr}")
        raise RuntimeError(f"ApartmentList ingestion script failed: {result.stderr}")
    
    context.log.info(f"Script output: {result.stdout}")
    
    # Parse output to find what was ingested
    # Expected format: "apartmentlist: latest=2025-09 rows=105 saved=data/silver/..."
    ingested_month = None
    row_count = 0
    
    for line in result.stdout.splitlines():
        if "latest=" in line and "rows=" in line:
            parts = line.split()
            for part in parts:
                if part.startswith("latest="):
                    ingested_month = part.split("=")[1]
                elif part.startswith("rows="):
                    row_count = int(part.split("=")[1])
    
    if not ingested_month:
        # Try to infer from directory structure
        silver_base = PROJECT_ROOT / "data" / "silver" / "apartmentlist"
        if silver_base.exists():
            date_dirs = sorted([d.name.replace("date=", "") 
                              for d in silver_base.glob("date=*") if d.is_dir()])
            if date_dirs:
                ingested_month = date_dirs[-1]
    
    if not ingested_month:
        raise RuntimeError("Could not determine ingested month from script output")
    
    context.log.info(f"Ingested month: {ingested_month}, rows: {row_count}")
    
    # Upload bronze layer to S3
    bronze_dir = PROJECT_ROOT / "data" / "bronze" / "apartmentlist" / f"date={ingested_month}"
    bronze_uris = []
    
    if bronze_dir.exists():
        context.log.info(f"Uploading bronze layer from {bronze_dir}")
        for csv_file in bronze_dir.glob("*.csv"):
            uri = s3.upload_partitioned_data(
                source="apartmentlist",
                layer="bronze",
                date=ingested_month,
                local_path=csv_file
            )
            bronze_uris.append(uri)
            context.log.info(f"Uploaded bronze: {uri}")
    else:
        context.log.warning(f"Bronze directory not found: {bronze_dir}")
    
    # Upload silver layer to S3
    silver_dir = PROJECT_ROOT / "data" / "silver" / "apartmentlist" / f"date={ingested_month}"
    silver_uris = []
    
    if silver_dir.exists():
        context.log.info(f"Uploading silver layer from {silver_dir}")
        for parquet_file in silver_dir.glob("*.parquet"):
            uri = s3.upload_partitioned_data(
                source="apartmentlist",
                layer="silver",
                date=ingested_month,
                local_path=parquet_file
            )
            silver_uris.append(uri)
            context.log.info(f"Uploaded silver: {uri}")
    else:
        context.log.warning(f"Silver directory not found: {silver_dir}")
    
    metadata = {
        "ingested_month": MetadataValue.text(ingested_month),
        "row_count": MetadataValue.int(row_count),
        "bronze_files_uploaded": MetadataValue.int(len(bronze_uris)),
        "silver_files_uploaded": MetadataValue.int(len(silver_uris)),
        "bronze_s3_paths": MetadataValue.md("\n".join(f"- `{uri}`" for uri in bronze_uris)),
        "silver_s3_paths": MetadataValue.md("\n".join(f"- `{uri}`" for uri in silver_uris)),
        "run_timestamp": MetadataValue.timestamp(datetime.now().timestamp()),
    }
    
    return Output(
        value={
            "month": ingested_month,
            "rows": row_count,
            "bronze_uris": bronze_uris,
            "silver_uris": silver_uris,
        },
        metadata=metadata,
    )


@asset(
    group_name="ingestion",
    description="Download and process FRED economic data for Tampa metro area",
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=60 * 24 * 32),  # ~1 month
    metadata={
        "source": "FRED",
        "update_frequency": "monthly",
        "layer": "bronze_silver",
    },
)
def fred_ingestion(
    context: AssetExecutionContext,
    s3: S3Resource,
) -> Output[dict[str, Any]]:
    """
    Run FRED ingestion script and upload outputs to S3.
    
    This asset:
    1. Executes ingest/fred_tampa_rent_pull.py to fetch Tampa CPI rent data
    2. Saves to bronze (raw JSON) and silver (Parquet) layers
    3. Uploads both layers to S3 with date partitioning
    4. Returns metadata about the ingestion run
    
    Bronze: data/bronze/fred/date=YYYY-MM/*.json
    Silver: data/silver/fred/date=YYYY-MM/*.parquet
    
    S3 Structure: fred/bronze/date=YYYY-MM/ and fred/silver/date=YYYY-MM/
    """
    script_path = INGEST_DIR / "fred_tampa_rent_pull.py"
    
    if not script_path.exists():
        raise FileNotFoundError(f"FRED ingestion script not found: {script_path}")
    
    context.log.info(f"Running FRED ingestion script: {script_path}")
    
    # Run the ingestion script with API key from environment
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env={**subprocess.os.environ, "FRED_API_KEY": subprocess.os.getenv("FRED_API_KEY", "")}
    )
    
    if result.returncode != 0:
        context.log.error(f"Script failed with exit code {result.returncode}")
        context.log.error(f"STDOUT: {result.stdout}")
        context.log.error(f"STDERR: {result.stderr}")
        raise RuntimeError(f"FRED ingestion script failed: {result.stderr}")
    
    context.log.info(f"Script output: {result.stdout}")
    
    # Parse output to find what was ingested
    # Expected format: "fred: latest=2024-01 rows=5 saved=data/silver/..."
    ingested_month = None
    row_count = 0
    
    for line in result.stdout.splitlines():
        if "latest=" in line and "rows=" in line:
            parts = line.split()
            for part in parts:
                if part.startswith("latest="):
                    ingested_month = part.split("=")[1]
                elif part.startswith("rows="):
                    row_count = int(part.split("=")[1])
    
    if not ingested_month:
        # Try to infer from directory structure
        silver_base = PROJECT_ROOT / "data" / "silver" / "fred"
        if silver_base.exists():
            date_dirs = sorted([d.name.replace("date=", "") 
                              for d in silver_base.glob("date=*") if d.is_dir()])
            if date_dirs:
                ingested_month = date_dirs[-1]
    
    if not ingested_month:
        raise RuntimeError("Could not determine ingested month from script output")
    
    context.log.info(f"Ingested month: {ingested_month}, rows: {row_count}")
    
    # Upload bronze layer to S3
    bronze_dir = PROJECT_ROOT / "data" / "bronze" / "fred" / f"date={ingested_month}"
    bronze_uris = []
    
    if bronze_dir.exists():
        context.log.info(f"Uploading bronze layer from {bronze_dir}")
        for json_file in bronze_dir.glob("*.json"):
            uri = s3.upload_partitioned_data(
                source="fred",
                layer="bronze",
                date=ingested_month,
                local_path=json_file
            )
            bronze_uris.append(uri)
            context.log.info(f"Uploaded bronze: {uri}")
    else:
        context.log.warning(f"Bronze directory not found: {bronze_dir}")
    
    # Upload silver layer to S3
    silver_dir = PROJECT_ROOT / "data" / "silver" / "fred" / f"date={ingested_month}"
    silver_uris = []
    
    if silver_dir.exists():
        context.log.info(f"Uploading silver layer from {silver_dir}")
        for parquet_file in silver_dir.glob("*.parquet"):
            uri = s3.upload_partitioned_data(
                source="fred",
                layer="silver",
                date=ingested_month,
                local_path=parquet_file
            )
            silver_uris.append(uri)
            context.log.info(f"Uploaded silver: {uri}")
    else:
        context.log.warning(f"Silver directory not found: {silver_dir}")
    
    metadata = {
        "ingested_month": MetadataValue.text(ingested_month),
        "row_count": MetadataValue.int(row_count),
        "bronze_files_uploaded": MetadataValue.int(len(bronze_uris)),
        "silver_files_uploaded": MetadataValue.int(len(silver_uris)),
        "bronze_s3_paths": MetadataValue.md("\n".join(f"- `{uri}`" for uri in bronze_uris)),
        "silver_s3_paths": MetadataValue.md("\n".join(f"- `{uri}`" for uri in silver_uris)),
        "run_timestamp": MetadataValue.timestamp(datetime.now().timestamp()),
    }
    
    return Output(
        value={
            "month": ingested_month,
            "rows": row_count,
            "bronze_uris": bronze_uris,
            "silver_uris": silver_uris,
        },
        metadata=metadata,
    )


# List of ingestion assets to export
ingestion_assets = [
    zillow_zori_ingestion,
    apartmentlist_ingestion,
    fred_ingestion,
]

