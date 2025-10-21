#!/usr/bin/env python3
"""
Convert Zillow ZORI Metro wide format CSV to standardized long format.

This script takes a wide format CSV from Zillow with date columns and converts 
it to a standardized long format suitable for Snowflake loading.
"""

import argparse
import re
import sys
from pathlib import Path
import pandas as pd


def convert_zillow_wide_to_long(input_path: str, output_path: str) -> bool:
    """
    Convert Zillow wide format CSV to long format.
    
    Args:
        input_path: Path to input wide format CSV
        output_path: Path to save long format CSV
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        if not input_file.exists():
            print(f"Error: Input file not found: {input_file}")
            return False
        
        print(f"Reading wide format CSV: {input_file}")
        df = pd.read_csv(input_file)
        
        print(f"Original shape: {df.shape}")
        print(f"Columns: {list(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
        
        # Define ID columns for Zillow Metro ZORI data
        id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
        
        # Verify ID columns exist
        missing_ids = [col for col in id_cols if col not in df.columns]
        if missing_ids:
            print(f"Error: Missing required ID columns: {missing_ids}")
            return False
        
        # Identify date columns (format: YYYY-MM-DD)
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        date_cols = [col for col in df.columns if date_pattern.match(col)]
        
        if not date_cols:
            print("Error: No date columns found (expected format: YYYY-MM-DD)")
            return False
        
        print(f"Found {len(date_cols)} date columns")
        print(f"Date range: {min(date_cols)} to {max(date_cols)}")
        
        # Melt wide to long format
        print("Converting wide format to long format...")
        long_df = df.melt(
            id_vars=id_cols,
            value_vars=date_cols,
            var_name='month',
            value_name='zori'
        )
        
        # Convert month to proper date format
        long_df['month'] = pd.to_datetime(long_df['month']).dt.date
        
        # Rename columns to match Snowflake schema
        long_df = long_df.rename(columns={
            'RegionName': 'METRO',
            'RegionType': 'REGION_TYPE', 
            'StateName': 'STATE_NAME',
            'RegionID': 'REGIONID',
            'SizeRank': 'SIZERANK'
        })
        
        # Select final columns in proper order
        final_cols = ['REGIONID', 'SIZERANK', 'METRO', 'REGION_TYPE', 'STATE_NAME', 'month', 'zori']
        result_df = long_df[final_cols].copy()
        
        # Remove rows with null ZORI values
        initial_rows = len(result_df)
        result_df = result_df.dropna(subset=['zori'])
        final_rows = len(result_df)
        
        if initial_rows != final_rows:
            print(f"Removed {initial_rows - final_rows:,} rows with null ZORI values")
        
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save long format CSV
        result_df.to_csv(output_file, index=False)
        
        # Print summary
        print(f"Converted shape: {result_df.shape}")
        print(f"Final rows: {len(result_df):,}")
        
        if 'month' in result_df.columns and not result_df['month'].isna().all():
            min_month = result_df['month'].min()
            max_month = result_df['month'].max()
            print(f"Date range: {min_month} to {max_month}")
        
        print(f"Saved long format CSV: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error converting CSV: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert Zillow ZORI Metro wide format CSV to long format"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="zori_metro_wide.csv",
        help="Input wide format CSV file"
    )
    parser.add_argument(
        "output_file",
        nargs="?", 
        default="zori_metro_long.csv",
        help="Output long format CSV file"
    )
    
    args = parser.parse_args()
    
    print(f"Converting Zillow ZORI Metro CSV:")
    print(f"  Input:  {args.input_file}")
    print(f"  Output: {args.output_file}")
    
    success = convert_zillow_wide_to_long(args.input_file, args.output_file)
    
    if success:
        print("Conversion completed successfully!")
        sys.exit(0)
    else:
        print("Conversion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()