#!/usr/bin/env python3
"""
ingest/zillow_zori_pull.py

Download and transform the latest Zillow Observed Rent Index (ZORI) data for the
Tampa, FL area.  This script discovers the latest CSV links on Zillow's research
data page each run (paths change periodically),
downloads city/metro/ZIP ZORI files, filters them to Tampa regions, and writes
bronze (raw CSV) and silver (tidy Parquet) outputs.

Usage:
    python ingest/zillow_zori_pull.py [--month YYYY-MM] [--force]

If --month is omitted, the script infers the latest available month by examining
the downloaded files and comparing with existing silver partitions.  The script
is idempotent: running it twice on the same month will not duplicate rows in the
silver layer.
"""

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from dateutil import parser as dateparser

# Configuration
USER_AGENT = (
    "tampa-rent-ingest/1.0 (+https://www.example.com; data engineer automation)"
)
BASE_URL = "https://www.zillow.com/research/data/"
SOURCE_NAME = "zillow_zori"
BRONZE_BASE = Path("data/bronze") / SOURCE_NAME
SILVER_BASE = Path("data/silver") / SOURCE_NAME


def create_session() -> requests.Session:
    """Configure a requests Session with retry/backoff."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def discover_zori_csv_links(html: str) -> List[Tuple[str, str]]:
    """
    Parse Zillow research data page HTML and return a list of tuples:
    (anchor_text, csv_url) for ZORI city/metro/ZIP CSV files.

    The page includes many CSVs for various housing datasets; we look for
    hrefs containing 'public_csvs' and 'zori'.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Look for ZORI CSVs - they can be in different formats
        if "zori" in href.lower() and ".csv" in href.lower():
            # Ensure absolute URL
            csv_url = href if href.startswith("http") else f"https://www.zillow.com{href}"
            anchor_text = (a.get_text() or "").strip()
            
            # Determine the type from the filename or surrounding context
            # Look for City/Metro/ZIP indicators in the URL or link text
            href_lower = href.lower()
            if "metro" in href_lower or "city" in href_lower or "zip" in href_lower:
                # Try to determine what type from the filename
                if "metro" in href_lower:
                    type_label = "Metro"
                elif "city" in href_lower:
                    type_label = "City"  
                elif "zip" in href_lower:
                    type_label = "ZIP"
                else:
                    type_label = "Metro"  # Default to Metro
                    
                # Create a descriptive anchor text if it's just "Download"
                if not anchor_text or anchor_text.lower() == "download":
                    anchor_text = f"{type_label} ZORI"
                    
                links.append((anchor_text, csv_url))
    return links


def download_csv(session: requests.Session, url: str, out_path: Path) -> None:
    """Stream a CSV file to disk."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def latest_month_from_df(df: pd.DataFrame) -> str:
    """Infer the most recent month (YYYY-MM) from a wide ZORI file."""
    # Date columns are typically formatted like "2025-09-30" or "2025-09".
    date_cols = [
        c
        for c in df.columns
        if re.match(r"\d{4}-\d{2}(-\d{2})?$", str(c))
        or re.match(r"\d{4}-\d{2}$", str(c))
    ]
    if not date_cols:
        raise ValueError("Could not find date columns in ZORI CSV.")
    # Convert to datetime and take max
    parsed_dates = [dateparser.parse(c).date() for c in date_cols]
    latest_dt = max(parsed_dates)
    return latest_dt.strftime("%Y-%m")


def tidy_zori(
    df: pd.DataFrame,
    region_type_filter: List[str],
    region_name_filter: List[str],
    region_id_prefixes: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Convert a wide ZORI dataframe into tidy long format.

    region_type_filter: list of lower-case region_type values to keep (e.g., ['msa', 'city'])
    region_name_filter: list of region names (case-insensitive) to keep
    region_id_prefixes: optional list of ZIP prefixes to match (for zip-level files)
    """
    # Normalize column names - strip whitespace
    df.columns = [c.strip() for c in df.columns]
    
    # Map PascalCase column names to snake_case
    column_mapping = {
        "RegionID": "region_id",
        "SizeRank": "size_rank",
        "RegionName": "region_name",
        "RegionType": "region_type",
        "StateName": "state",
    }
    
    # Rename columns to snake_case
    df = df.rename(columns=column_mapping)
    
    # Identify meta columns (region identifiers) and date columns
    meta_cols = [
        "region_type",
        "region_name",
        "region_id",
        "state",
        "size_rank",
    ]
    meta_cols_present = [c for c in meta_cols if c in df.columns]
    date_cols = [c for c in df.columns if c not in meta_cols_present]
    
    # Filter rows by region type/name/zip prefix
    filt_df = df.copy()
    if region_type_filter:
        filt_df = filt_df[filt_df["region_type"].str.lower().isin(region_type_filter)]
    if region_name_filter:
        filt_df = filt_df[
            filt_df["region_name"].str.lower().isin([n.lower() for n in region_name_filter])
        ]
    if region_id_prefixes and "region_id" in filt_df.columns:
        filt_df = filt_df[filt_df["region_id"].astype(str).str.startswith(tuple(region_id_prefixes))]
    
    # Melt to long format
    long_df = filt_df.melt(
        id_vars=meta_cols_present,
        value_vars=date_cols,
        var_name="period",
        value_name="value",
    )
    
    # Standardize period to YYYY-MM
    long_df["period"] = long_df["period"].apply(
        lambda x: dateparser.parse(str(x)).strftime("%Y-%m")
    )
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
    long_df["source"] = SOURCE_NAME
    long_df["pulled_at"] = pd.Timestamp.utcnow()
    
    # Reorder columns
    final_cols = [
        "source",
        "region_type",
        "region_name",
        "region_id",
        "period",
        "value",
        "pulled_at",
    ]
    
    # fill missing columns if absent
    for col in final_cols:
        if col not in long_df.columns:
            long_df[col] = None
    
    return long_df[final_cols]


def load_existing_silver_months() -> List[str]:
    """List existing month partitions in the silver layer."""
    if not SILVER_BASE.exists():
        return []
    return sorted(
        {
            p.name.split("=")[-1]
            for p in SILVER_BASE.glob("date=*")
            if p.is_dir() and re.match(r"\d{4}-\d{2}", p.name.split("=")[-1])
        }
    )


def save_parquet(df: pd.DataFrame, out_path: Path) -> None:
    """Save a pandas DataFrame to a Parquet file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, out_path, compression="snappy")


def main(month: Optional[str], force: bool) -> None:
    session = create_session()
    # Fetch research page
    resp = session.get(BASE_URL, timeout=60)
    resp.raise_for_status()
    links = discover_zori_csv_links(resp.text)
    if not links:
        raise RuntimeError("No ZORI CSV links found on Zillow research page.")
    # Determine existing months
    existing_months = load_existing_silver_months()
    # Process each CSV (city/metro/zip)
    latest_periods = []
    tidy_frames = []
    for anchor_text, url in links:
        # Download raw CSV
        raw_df = None
        tmp_csv_path = None
        try:
            r = session.get(url, stream=True, timeout=60)
            r.raise_for_status()
            # Save to bronze for this run (month unspecified yet)
            raw_bytes = r.content
            # Read into pandas without saving to disk first
            from io import BytesIO

            raw_df = pd.read_csv(BytesIO(raw_bytes))
            latest = latest_month_from_df(raw_df)
            latest_periods.append(latest)
            # Determine the target month (use CLI override if provided)
            target_month = month or latest
            # Skip if target month already ingested and not forcing
            if (not force) and (target_month in existing_months):
                continue
            # Save raw CSV
            bronze_dir = BRONZE_BASE / f"date={target_month}"
            bronze_dir.mkdir(parents=True, exist_ok=True)
            # Derive filename from link anchor text
            slug = re.sub(r"\W+", "_", anchor_text.lower()).strip("_")
            tmp_csv_path = bronze_dir / f"{slug}.csv"
            with open(tmp_csv_path, "wb") as f:
                f.write(raw_bytes)
            # Transform to tidy
            if "zip" in anchor_text.lower():
                region_type_filter = ["zip"]
                region_name_filter = []  # Not filtering on name for ZIP-level
                region_id_prefixes = ["336"]  # Tampa ZIPs start with 336
            elif "metro" in anchor_text.lower():
                region_type_filter = ["msa"]
                region_name_filter = ["Tampa, FL"]  # Tampa metro area
                region_id_prefixes = None
            else:  # city
                region_type_filter = ["city"]
                region_name_filter = ["Tampa, FL"]
                region_id_prefixes = None
            tidy_df = tidy_zori(
                raw_df,
                region_type_filter=region_type_filter,
                region_name_filter=region_name_filter,
                region_id_prefixes=region_id_prefixes,
            )
            tidy_df["period"] = tidy_df["period"].astype(str)
            tidy_frames.append((target_month, tidy_df))
        except Exception as exc:
            print(f"Error processing {url}: {exc}", file=sys.stderr)
            continue
    if not tidy_frames:
        print("No new ZORI data to ingest.")
        return
    # For each month, combine frames and write silver
    for target_month, df in tidy_frames:
        silver_dir = SILVER_BASE / f"date={target_month}"
        silver_path = silver_dir / f"zori_tampa.parquet"
        save_parquet(df, silver_path)
        print(
            f"{SOURCE_NAME}: latest={target_month} rows={len(df)} saved={silver_path}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull Zillow ZORI data for Tampa.")
    parser.add_argument(
        "--month",
        help="Month to ingest (YYYY-MM); defaults to latest available.",
        required=False,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download and overwrite existing data for the month.",
    )
    args = parser.parse_args()
    main(args.month, args.force)

