#!/usr/bin/env python3
"""
ingest/apartmentlist_pull.py

Download and transform the latest Apartment List rent estimates for the
Tampa, FL area. The script scrapes the research page to find CSV download URLs
embedded in the dropdown options' data-value attributes, then downloads and
filters to Tampa.

Usage:
    python ingest/apartmentlist_pull.py [--month YYYY-MM] [--force]

No browser automation required - uses simple HTTP requests and BeautifulSoup.
"""

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
from typing import Optional, List
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Configuration
PAGE_URL = "https://www.apartmentlist.com/research/category/data-rent-estimates"
SOURCE_NAME = "apartmentlist"
BRONZE_BASE = Path("data/bronze") / SOURCE_NAME
SILVER_BASE = Path("data/silver") / SOURCE_NAME
USER_AGENT = "tampa-rent-ingest/1.0 (+https://www.example.com; data engineer automation)"


def create_session() -> requests.Session:
    """Create requests session with retry logic."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def discover_csv_urls(html: str) -> List[tuple]:
    """
    Extract CSV URLs directly from HTML using regex.
    
    The page embeds CSV URLs from assets.ctfassets.net directly in the HTML.
    We use regex to find them instead of relying on DOM structure.
    
    Returns list of (label, url) tuples.
    """
    csv_links = []
    
    # Pattern to find CSV URLs from Contentful CDN (the format ApartmentList uses)
    # Matches: //assets.ctfassets.net/.../filename.csv
    csv_pattern = re.compile(
        r'(//assets\.ctfassets\.net/[^\s\'"<>]+\.csv)',
        re.IGNORECASE
    )
    
    # Find all CSV URLs in the raw HTML
    matches = csv_pattern.findall(html)
    
    # De-duplicate and normalize
    unique_urls = sorted(set(matches))
    
    print(f"Found {len(unique_urls)} unique CSV URL(s) in HTML")
    
    for url in unique_urls:
        # Convert to absolute URL
        abs_url = "https:" + url if url.startswith("//") else url
        
        # Extract filename from URL
        filename = url.split("/")[-1]
        
        # Filter for the files we want
        # We want: Apartment_List_Rent_Estimates_YYYY_MM.csv (historic data)
        # We DON'T want: Summary or Growth files
        if "Apartment_List_Rent_Estimates_" in filename:
            if "Summary" not in filename and "Growth" not in filename:
                # This is the historic estimates file we want
                label = f"Historic Rent Estimates ({filename})"
                csv_links.append((label, abs_url))
                print(f"  ✓ Selected: {filename}")
            else:
                print(f"  ✗ Skipped: {filename} (not historic data)")
        else:
            print(f"  ✗ Skipped: {filename} (not rent estimates)")
    
    return csv_links


def download_csv(session: requests.Session, url: str, out_path: Path) -> bool:
    """Download CSV from URL and save to path."""
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading from {url[:100]}...")
        
        resp = session.get(url, timeout=60)
        resp.raise_for_status()
        
        out_path.write_bytes(resp.content)
        print(f"Saved to {out_path} ({len(resp.content)} bytes)")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def tidy_apartmentlist(
    df: pd.DataFrame,
    location_type: str,
    location_name: str,
) -> pd.DataFrame:
    """
    Convert Apartment List rent estimates to tidy format.

    The CSVs have columns like:
      location_name, location_type, location_fips_code, bed_size, 2017_01, 2017_02, ...
    This is a wide format that needs to be pivoted to long format.
    """
    # Normalize column names - strip quotes and whitespace
    df.columns = [c.strip().strip('"').lower() for c in df.columns]
    
    # Map ApartmentList column names to our standard names
    column_mapping = {
        "location_name": "region_name",
        "location_type": "region_type",
        "location_fips_code": "region_id",
    }
    df = df.rename(columns=column_mapping)
    
    # Filter for the specific location and type
    if "region_type" not in df.columns or "region_name" not in df.columns:
        raise RuntimeError(f"Missing region columns. Found: {df.columns.tolist()[:10]}")
    
    mask = (df["region_type"].str.lower() == location_type.lower())
    if mask.sum() == 0:
        print(f"  No rows match region_type='{location_type}'")
        print(f"  Available types: {df['region_type'].unique()[:10]}")
    
    # Also filter by name
    mask = mask & (df["region_name"].str.contains(location_name, case=False, na=False))
    
    df_filtered = df[mask].copy()
    
    if len(df_filtered) == 0:
        return pd.DataFrame()
    
    # Identify date columns (format: YYYY_MM)
    date_cols = [c for c in df_filtered.columns if re.match(r'\d{4}_\d{2}', c)]
    
    if not date_cols:
        raise RuntimeError(f"No date columns found (expected format: YYYY_MM)")
    
    # Keep identity columns
    id_cols = ["region_name", "region_type", "region_id", "bed_size"]
    id_cols = [c for c in id_cols if c in df_filtered.columns]
    
    # Melt to long format
    df_long = df_filtered.melt(
        id_vars=id_cols,
        value_vars=date_cols,
        var_name="period_raw",
        value_name="value"
    )
    
    # Convert period from "2017_01" to "2017-01"
    df_long["period"] = df_long["period_raw"].str.replace("_", "-")
    
    # Add metadata
    df_long["source"] = SOURCE_NAME
    df_long["pulled_at"] = pd.Timestamp.utcnow()
    
    # Convert value to numeric
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    
    # Select and order columns
    output_cols = ["source", "region_type", "region_name", "region_id", "bed_size", "period", "value", "pulled_at"]
    output_cols = [c for c in output_cols if c in df_long.columns]
    
    tidy = df_long[output_cols].copy()
    
    # Drop rows with missing values
    tidy = tidy.dropna(subset=["value"]).reset_index(drop=True)
    
    return tidy


def load_existing_silver_months() -> List[str]:
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, out_path, compression="snappy")


def main(month: Optional[str], force: bool) -> None:
    # Infer target month from filename or use current month - 1
    session = create_session()
    
    print(f"Fetching ApartmentList research page...")
    resp = session.get(PAGE_URL, timeout=60)
    resp.raise_for_status()
    
    # Discover CSV URLs
    csv_links = discover_csv_urls(resp.text)
    
    if not csv_links:
        print("ERROR: No CSV links found on ApartmentList page.")
        print("The page structure may have changed.")
        return
    
    print(f"\nFound {len(csv_links)} CSV link(s)")
    
    # Download the first historic rent estimates CSV
    label, url = csv_links[0]
    
    # Try to infer month from filename
    # Example: Apartment_List_Rent_Estimates_2025_09.csv
    filename_match = re.search(r'(\d{4})[_-](\d{2})\.csv', url)
    if filename_match and not month:
        target_month = f"{filename_match.group(1)}-{filename_match.group(2)}"
    elif month:
        target_month = month
    else:
        # Fallback to previous month
        today = dt.date.today()
        first = today.replace(day=1)
        last_month = first - dt.timedelta(days=1)
        target_month = last_month.strftime("%Y-%m")
    
    print(f"Target month: {target_month}")
    
    # Check existing
    existing_months = load_existing_silver_months()
    if (not force) and (target_month in existing_months):
        print(f"{SOURCE_NAME}: {target_month} already ingested. Skipping.")
        return
    
    # Download to bronze
    bronze_dir = BRONZE_BASE / f"date={target_month}"
    bronze_path = bronze_dir / "apartmentlist_historic.csv"
    
    if not download_csv(session, url, bronze_path):
        print("Failed to download ApartmentList CSV")
        return
    
    # Load and process
    print(f"\nProcessing {bronze_path}...")
    df = pd.read_csv(bronze_path)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Transform to tidy format and filter for Tampa
    # ApartmentList uses "Metro" (not "msa") for metro areas
    tampa_names = [
        "Tampa-St. Petersburg-Clearwater, FL",
        "Tampa, FL",
        "Tampa - St. Petersburg - Clearwater, FL",
        "Tampa"  # Try partial match too
    ]
    
    tidy_frames = []
    for tampa_name in tampa_names:
        try:
            tidy_df = tidy_apartmentlist(df, "Metro", tampa_name)
            if len(tidy_df) > 0:
                tidy_frames.append(tidy_df)
                print(f"✓ Found {len(tidy_df)} rows for {tampa_name}")
                break  # Found data, no need to try other variations
        except Exception as e:
            print(f"✗ No data for '{tampa_name}': {e}")
    
    if not tidy_frames:
        print("\nNo ApartmentList data for Tampa found.")
        print("Available metro areas in file:")
        df_norm = df.copy()
        df_norm.columns = [c.strip().lower().replace(" ", "_") for c in df_norm.columns]
        if "region_name" in df_norm.columns and "region_type" in df_norm.columns:
            metros = df_norm[df_norm["region_type"].str.lower() == "msa"]["region_name"].unique()
            fl_metros = [m for m in metros if "FL" in str(m)]
            print(f"Florida metros ({len(fl_metros)}): {fl_metros[:10]}")
        return
    
    # Combine all Tampa data
    combined = pd.concat(tidy_frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["period", "region_name"])
    
    # Write silver
    silver_dir = SILVER_BASE / f"date={target_month}"
    silver_path = silver_dir / "apartmentlist_tampa.parquet"
    save_parquet(combined, silver_path)
    print(f"\n{SOURCE_NAME}: latest={target_month} rows={len(combined)} saved={silver_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull Apartment List rent estimates for Tampa.")
    parser.add_argument(
        "--month",
        help="Month to ingest (YYYY-MM); defaults to the month shown on the page.",
        required=False,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download and overwrite existing data for the month.",
    )
    args = parser.parse_args()
    main(args.month, args.force)

