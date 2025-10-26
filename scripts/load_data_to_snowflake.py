#!/usr/bin/env python3
"""
Load data from local silver parquet files into Snowflake RAW tables
"""
import snowflake.connector
import pandas as pd
from pathlib import Path
from datetime import datetime

print("="*60)
print("LOADING DATA INTO SNOWFLAKE RAW TABLES")
print("="*60)

# Snowflake connection
conn = snowflake.connector.connect(
    account='mvc20409.us-east-1',
    user='DRAKEDAMON',
    password='SnowflakeFreedom2027!',
    database='RENTS',
    schema='RAW',
    warehouse='WH_XS',
    role='ACCOUNTADMIN'
)

cursor = conn.cursor()

# Import pandas tools for bulk loading
from snowflake.connector.pandas_tools import write_pandas

# 1. Load ApartmentList data
print("\n1. Loading ApartmentList data...")
apt_file = Path("data/silver/apartmentlist/date=2025-09/apartmentlist_tampa.parquet")
if apt_file.exists():
    df_apt = pd.read_parquet(apt_file)
    print(f"   Read {len(df_apt)} rows from silver parquet")
    
    # Map silver columns to RAW schema
    # Silver: source, region_type, region_name, region_id, bed_size, period, value, pulled_at
    # RAW needs: location_fips_code, regionid, location_name, location_type, state, county, metro, month, rent_index, population
    
    df_load = pd.DataFrame({
        'LOCATION_FIPS_CODE': df_apt['region_id'],
        'REGIONID': df_apt['bed_size'],
        'LOCATION_NAME': df_apt['region_name'],
        'LOCATION_TYPE': df_apt['region_type'],
        'STATE': None,
        'COUNTY': None,
        'METRO': df_apt['region_name'],
        'MONTH': pd.to_datetime(df_apt['period'], format='%Y-%m').dt.date,
        'RENT_INDEX': df_apt['value'],
        'POPULATION': None,
        'S3_FILE_PATH': 's3://rent-signals-dev-dd/apartmentlist/bronze/date=2025-09/apartmentlist_historic.csv'
    }).reset_index(drop=True)
    
    success, nchunks, nrows, _ = write_pandas(
        conn, df_load, 'APTLIST_LONG', schema='RAW', database='RENTS'
    )
    print(f"   ✅ Loaded {nrows} rows into APTLIST_LONG")
else:
    print(f"   ⚠️  File not found: {apt_file}")

# 2. Load FRED data
print("\n2. Loading FRED data...")
fred_file = Path("data/silver/fred/date=2025-09/fred_tampa_rent.parquet")
if fred_file.exists():
    df_fred = pd.read_parquet(fred_file)
    print(f"   Read {len(df_fred)} rows from silver parquet")
    
    # Map silver columns to RAW schema
    # Silver: source, region_type, region_name, region_id, series_title, period, value, pulled_at
    # RAW needs: series_id, label, month, value
    
    df_load = pd.DataFrame({
        'SERIES_ID': df_fred['region_id'],
        'LABEL': df_fred.get('series_title', 'CPI-U Rent of Primary Residence (NSA, 1982-84=100)'),
        'MONTH': pd.to_datetime(df_fred['period'], format='%Y-%m').dt.date,
        'VALUE': df_fred['value'],
        'S3_FILE_PATH': 's3://rent-signals-dev-dd/fred/bronze/date=2025-09/CUUR0000SEHA.json'
    }).reset_index(drop=True)
    
    success, nchunks, nrows, _ = write_pandas(
        conn, df_load, 'FRED_CPI_LONG', schema='RAW', database='RENTS'
    )
    print(f"   ✅ Loaded {nrows} rows into FRED_CPI_LONG")
else:
    print(f"   ⚠️  File not found: {fred_file}")

# 3. Verify all tables
print("\n3. Verifying data loaded...")
cursor.execute("""
    SELECT 'ZORI_METRO_LONG' as table_name, COUNT(*) as row_count FROM RENTS.RAW.ZORI_METRO_LONG
    UNION ALL
    SELECT 'APTLIST_LONG', COUNT(*) FROM RENTS.RAW.APTLIST_LONG
    UNION ALL
    SELECT 'FRED_CPI_LONG', COUNT(*) FROM RENTS.RAW.FRED_CPI_LONG
    ORDER BY table_name
""")
counts = cursor.fetchall()
print("\n   Row counts:")
for row in counts:
    print(f"   {row[0]}: {row[1]:,} rows")

# 4. Check sample data
print("\n4. Sample data from each table:")
print("\n   APTLIST_LONG sample:")
cursor.execute("SELECT LOCATION_NAME, REGIONID, MONTH, RENT_INDEX FROM RENTS.RAW.APTLIST_LONG LIMIT 3")
for row in cursor.fetchall():
    print(f"     {row[0]}, {row[1]}, {row[2]}, ${row[3]}")

print("\n   FRED_CPI_LONG sample:")
cursor.execute("SELECT SERIES_ID, MONTH, VALUE FROM RENTS.RAW.FRED_CPI_LONG LIMIT 3")
for row in cursor.fetchall():
    print(f"     {row[0]}, {row[1]}, {row[2]}")

cursor.close()
conn.close()

print("\n" + "="*60)
print("✅ DATA LOADED SUCCESSFULLY!")
print("="*60)
print("\nNext: Run dbt pipeline")
print("  cd dbt_rent_signals")
print("  dbt run --select staging core marts")
print("  dbt test")

