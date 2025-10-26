#!/usr/bin/env python3
"""
ingest/fred_tampa_rent_pull.py

Fetch observations for the national CPI-U series "Rent of primary residence in
U.S. city average" (series_id=CUUR0000SEHA) from FRED via their official API.
The series is monthly and not seasonally adjusted (Index 1982-1984 = 100).

This script retrieves monthly observations, saves raw JSON to bronze and writes
a tidy Parquet to silver. The national CPI data can be used as a proxy for
regional rent inflation trends.

Usage:
    python ingest/fred_tampa_rent_pull.py [--force]

The script fetches the last 5 years of monthly data and uses the latest
observation date as the partition key.
"""

import argparse
import datetime as dt
import os
import json
from pathlib import Path
from typing import Optional, List
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Configuration
API_BASE = "https://api.stlouisfed.org/fred/series/observations"
SERIES_ID = "CUUR0000SEHA"  # National CPI-U Rent of Primary Residence, monthly, NSA
SOURCE_NAME = "fred"
BRONZE_BASE = Path("data/bronze") / SOURCE_NAME
SILVER_BASE = Path("data/silver") / SOURCE_NAME
USER_AGENT = (
    "tampa-rent-ingest/1.0 (+https://www.example.com; data engineer automation)"
)

def create_session() -> requests.Session:
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


def fetch_observations(api_key: Optional[str] = None) -> dict:
    params = {
        "series_id": SERIES_ID,
        "file_type": "json",
    }
    if api_key:
        params["api_key"] = api_key
    # Only request data from the last 5 years
    today = dt.date.today()
    params["observation_start"] = (today.replace(year=today.year - 5)).isoformat()
    session = create_session()
    resp = session.get(API_BASE, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def load_existing_months() -> List[str]:
    if not SILVER_BASE.exists():
        return []
    return sorted(
        {
            p.name.split("=")[-1]
            for p in SILVER_BASE.glob("date=*")
            if p.is_dir()
        }
    )


def save_parquet(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, out_path, compression="snappy")


def main(force: bool) -> None:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        print("ERROR: FRED_API_KEY environment variable is required.")
        print("\nTo get a free API key:")
        print("1. Visit: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("2. Sign up for a free account")
        print("3. Request an API key (instant approval)")
        print("4. Set environment variable: export FRED_API_KEY=your_key_here")
        print("\nThen run this script again.")
        return
    
    print(f"Fetching FRED data for series: {SERIES_ID}")
    data = fetch_observations(api_key)
    observations = data.get("observations", [])
    
    if not observations:
        print("No observations returned from FRED API.")
        return
    
    print(f"Received {len(observations)} observations from FRED")
    
    # Convert to DataFrame
    obs_df = pd.DataFrame(observations)
    # Use last observation as latest (the series is annual)
    obs_df["date"] = pd.to_datetime(obs_df["date"])
    obs_df["value"] = pd.to_numeric(obs_df["value"], errors="coerce")
    obs_df.sort_values("date", inplace=True)
    
    latest_row = obs_df.iloc[-1]
    latest_period = latest_row["date"].strftime("%Y-%m")
    
    print(f"Latest observation date: {latest_period}, value: {latest_row['value']}")
    
    # Skip if already ingested and not forcing
    existing = load_existing_months()
    if (not force) and (latest_period in existing):
        print(f"{SOURCE_NAME}: {latest_period} already ingested. Skipping.")
        return
    
    # Save bronze JSON
    bronze_dir = BRONZE_BASE / f"date={latest_period}"
    bronze_dir.mkdir(parents=True, exist_ok=True)
    json_path = bronze_dir / f"{SERIES_ID}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved bronze JSON: {json_path}")
    
    # Build tidy DataFrame (use all observations)
    obs_df["period"] = obs_df["date"].dt.strftime("%Y-%m")
    tidy_df = pd.DataFrame({
        "source": SOURCE_NAME,
        "region_type": "national",
        "region_name": "U.S. City Average",
        "region_id": SERIES_ID,
        "series_title": "CPI-U Rent of Primary Residence (NSA, 1982-84=100)",
        "period": obs_df["period"],
        "value": obs_df["value"],
        "pulled_at": pd.Timestamp.utcnow(),
    })
    
    # Save silver parquet
    silver_dir = SILVER_BASE / f"date={latest_period}"
    silver_path = silver_dir / f"fred_tampa_rent.parquet"
    save_parquet(tidy_df, silver_path)
    print(f"{SOURCE_NAME}: latest={latest_period} rows={len(tidy_df)} saved={silver_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull FRED Tampa rent CPI data.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download and overwrite existing data for the latest period.",
    )
    args = parser.parse_args()
    main(args.force)

