#!/usr/bin/env python3
"""
Normalize Apartment List CSV data to consistent long format.

This script takes a CSV file from Apartment List (either wide or long format)
and converts it to a standardized long format with 9 columns.
"""

import argparse
import re
import sys
from pathlib import Path
import pandas as pd


def detect_format(df: pd.DataFrame) -> str:
    """
    Detect if the CSV is in long or wide format.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        str: 'long' if already in long format, 'wide' if needs transformation
    """
    cols = [c.lower().strip() for c in df.columns]
    
    # Check for long format indicators
    has_month = any('month' in col for col in cols)
    has_rent_index = any('rent_index' in col or 'rent index' in col for col in cols)
    
    if has_month and has_rent_index:
        return 'long'
    
    # Check for wide format indicators (date columns)
    date_pattern = re.compile(r'^\d{4}[-_]\d{2}([-_]\d{2})?$')
    date_cols = [col for col in df.columns if date_pattern.match(col)]
    
    if len(date_cols) > 3:  # Arbitrary threshold
        return 'wide'
    
    # Default to assuming it needs transformation
    return 'wide'


def normalize_long_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize a CSV that's already in long format.
    
    Args:
        df: DataFrame in long format
        
    Returns:
        pd.DataFrame: Standardized long format DataFrame
    """
    print("Data is already in long format, standardizing column names...")
    
    # Define column name mappings
    rename_map = {
        'location name': 'location_name',
        'location': 'location_name',
        'location_type': 'location_type',
        'location fips code': 'location_fips_code',
        'location_fips_code': 'location_fips_code',
        'population': 'population',
        'state': 'state',
        'county': 'county',
        'metro': 'metro',
        'rent_index': 'rent_index',
        'rent index': 'rent_index',
        'month': 'month'
    }
    
    # Normalize column names (case insensitive)
    df_normalized = df.rename(columns={
        col: rename_map.get(col.lower().strip(), col) 
        for col in df.columns
    })
    
    # Ensure all required columns exist
    required_columns = [
        'location_name', 'location_type', 'location_fips_code', 'population',
        'state', 'county', 'metro', 'rent_index', 'month'
    ]
    
    for col in required_columns:
        if col not in df_normalized.columns:
            df_normalized[col] = None
    
    # Select and reorder columns
    result = df_normalized[required_columns].copy()
    
    # Convert month to date format if needed
    if result['month'].dtype == 'object':
        try:
            result['month'] = pd.to_datetime(result['month']).dt.date
        except:
            print("Warning: Could not convert month column to date format")
    
    return result


def normalize_wide_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert wide format CSV to standardized long format.
    
    Args:
        df: DataFrame in wide format
        
    Returns:
        pd.DataFrame: Standardized long format DataFrame
    """
    print("Data is in wide format, converting to long format...")
    
    # Normalize column names for easier detection
    df_normalized = df.rename(columns={c: c.lower().strip() for c in df.columns})
    
    # Identify ID columns
    id_candidates = [
        'location_name', 'location name', 'location_type', 'location type',
        'location_fips_code', 'location fips code', 'population',
        'state', 'county', 'metro'
    ]
    
    id_cols = [col for col in df_normalized.columns if col in id_candidates]
    
    # Fallback to common columns if none found
    if not id_cols:
        id_cols = [col for col in df_normalized.columns 
                  if col in ['location_name', 'state', 'county', 'metro']]
    
    if not id_cols:
        print("Warning: No ID columns detected, using first column as identifier")
        id_cols = [df_normalized.columns[0]]
    
    # Identify date columns
    date_pattern = re.compile(r'^\d{4}[-_]\d{2}([-_]\d{2})?$')
    date_cols = [col for col in df_normalized.columns if date_pattern.match(col)]
    
    if not date_cols:
        raise ValueError("No date columns found to melt")
    
    print(f"Found {len(id_cols)} ID columns and {len(date_cols)} date columns")
    print(f"ID columns: {id_cols}")
    print(f"Date range: {min(date_cols)} to {max(date_cols)}")
    
    # Melt the DataFrame
    long_df = df_normalized.melt(
        id_vars=id_cols,
        value_vars=date_cols,
        var_name='month',
        value_name='rent_index'
    )
    
    # Convert month column to proper date format
    long_df['month'] = pd.to_datetime(
        long_df['month'].str.replace('_', '-')
    ).dt.date
    
    # Create standardized DataFrame
    result = pd.DataFrame({
        'location_name': long_df.get('location_name', long_df.get('location name')),
        'location_type': long_df.get('location_type', long_df.get('location type')),
        'location_fips_code': long_df.get('location_fips_code', long_df.get('location fips code')),
        'population': long_df.get('population'),
        'state': long_df.get('state'),
        'county': long_df.get('county'),
        'metro': long_df.get('metro'),
        'rent_index': long_df['rent_index'],
        'month': long_df['month']
    })
    
    return result


def normalize_apartmentlist_csv(input_path: str, output_path: str) -> bool:
    """
    Normalize Apartment List CSV to standardized long format.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to save normalized CSV
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        if not input_file.exists():
            print(f"Error: Input file not found: {input_file}")
            return False
        
        print(f"Reading CSV from: {input_file}")
        df = pd.read_csv(input_file)
        
        print(f"Original shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Detect format and normalize accordingly
        format_type = detect_format(df)
        print(f"Detected format: {format_type}")
        
        if format_type == 'long':
            normalized_df = normalize_long_format(df)
        else:
            normalized_df = normalize_wide_format(df)
        
        # Remove rows with null rent_index
        initial_rows = len(normalized_df)
        normalized_df = normalized_df.dropna(subset=['rent_index'])
        final_rows = len(normalized_df)
        
        if initial_rows != final_rows:
            print(f"Removed {initial_rows - final_rows:,} rows with null rent_index")
        
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save normalized CSV
        normalized_df.to_csv(output_file, index=False)
        
        # Print summary
        print(f"Normalized shape: {normalized_df.shape}")
        print(f"Final rows: {len(normalized_df):,}")
        
        if 'month' in normalized_df.columns and not normalized_df['month'].isna().all():
            min_month = normalized_df['month'].min()
            max_month = normalized_df['month'].max()
            print(f"Date range: {min_month} to {max_month}")
        
        print(f"Saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error normalizing CSV: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Normalize Apartment List CSV to standardized long format"
    )
    parser.add_argument(
        "--in",
        dest="input_file",
        default="data/apartmentlist_raw.csv",
        help="Input CSV file path"
    )
    parser.add_argument(
        "--out",
        dest="output_file", 
        default="data/apartmentlist_long.csv",
        help="Output CSV file path"
    )
    
    args = parser.parse_args()
    
    print(f"Normalizing Apartment List CSV:")
    print(f"  Input: {args.input_file}")
    print(f"  Output: {args.output_file}")
    
    success = normalize_apartmentlist_csv(args.input_file, args.output_file)
    
    if success:
        print("Normalization completed successfully!")
        sys.exit(0)
    else:
        print("Normalization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()