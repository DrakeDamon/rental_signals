#!/usr/bin/env python3
"""
Fix Snowflake RAW tables to match the documented schema in load_from_s3_bronze.sql
This will DROP and recreate tables with the correct structure.
"""
import snowflake.connector
import pandas as pd
from pathlib import Path

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

print("="*60)
print("FIXING SNOWFLAKE RAW SCHEMA")
print("="*60)

# Drop existing tables with wrong schema
print("\n1. Dropping existing tables with incorrect schema...")
cursor.execute("DROP TABLE IF EXISTS RENTS.RAW.APTLIST_LONG")
print("   ✅ Dropped APTLIST_LONG")

cursor.execute("DROP TABLE IF EXISTS RENTS.RAW.FRED_CPI_LONG")
print("   ✅ Dropped FRED_CPI_LONG")

# Create tables with CORRECT schema matching load_from_s3_bronze.sql
print("\n2. Creating tables with correct schema...")

# ApartmentList - should have REGIONID (bed_size in bronze becomes regionid)
cursor.execute("""
    CREATE TABLE RENTS.RAW.APTLIST_LONG (
      LOCATION_FIPS_CODE VARCHAR(20),
      REGIONID VARCHAR(50),  -- This will be bed_size from source
      LOCATION_NAME VARCHAR(255),
      LOCATION_TYPE VARCHAR(50),
      STATE VARCHAR(100),
      COUNTY VARCHAR(100),
      METRO VARCHAR(255),
      MONTH DATE,
      RENT_INDEX DECIMAL(10, 2),
      POPULATION INTEGER,
      LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
      S3_FILE_PATH VARCHAR(500)
    )
""")
print("   ✅ Created APTLIST_LONG with correct schema")

# FRED - should have SERIES_ID, LABEL, MONTH, VALUE
cursor.execute("""
    CREATE TABLE RENTS.RAW.FRED_CPI_LONG (
      SERIES_ID VARCHAR(50),
      LABEL VARCHAR(500),
      MONTH DATE,
      VALUE DECIMAL(18, 4),
      LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
      S3_FILE_PATH VARCHAR(500)
    )
""")
print("   ✅ Created FRED_CPI_LONG with correct schema")

# Add clustering
print("\n3. Adding clustering keys...")
cursor.execute("ALTER TABLE RENTS.RAW.APTLIST_LONG CLUSTER BY (MONTH, LOCATION_NAME)")
cursor.execute("ALTER TABLE RENTS.RAW.FRED_CPI_LONG CLUSTER BY (SERIES_ID, MONTH)")
print("   ✅ Clustering keys added")

# Load data from local silver parquet files (transformed data)
print("\n4. Loading data from silver layer...")

# Load ApartmentList from silver parquet
print("\n   Loading ApartmentList...")
apt_file = Path("data/silver/apartmentlist/date=2025-09/apartmentlist_tampa.parquet")
if apt_file.exists():
    df_apt = pd.read_parquet(apt_file)
    print(f"   Found {len(df_apt)} rows in silver parquet")
    print(f"   Columns: {df_apt.columns.tolist()}")
    
    # Map silver columns to RAW schema
    # Silver has: source, region_type, region_name, region_id, bed_size, period, value, pulled_at
    # RAW needs: location_fips_code, regionid, location_name, location_type, state, county, metro, month, rent_index, population
    
    df_load = pd.DataFrame({
        'LOCATION_FIPS_CODE': df_apt.get('region_id', ''),
        'REGIONID': df_apt.get('bed_size', ''),
        'LOCATION_NAME': df_apt.get('region_name', ''),
        'LOCATION_TYPE': df_apt.get('region_type', ''),
        'STATE': None,
        'COUNTY': None,
        'METRO': df_apt.get('region_name', ''),
        'MONTH': pd.to_datetime(df_apt['period']).dt.date,
        'RENT_INDEX': df_apt['value'],
        'POPULATION': None,
        'S3_FILE_PATH': 's3://rent-signals-dev-dd/apartmentlist/bronze/date=2025-09/apartmentlist_historic.csv'
    })
    
    # Write to Snowflake
    from snowflake.connector.pandas_tools import write_pandas
    success, nchunks, nrows, _ = write_pandas(
        conn, df_load, 'APTLIST_LONG', schema='RAW', database='RENTS'
    )
    print(f"   ✅ Loaded {nrows} rows into APTLIST_LONG")
else:
    print(f"   ⚠️  Silver file not found: {apt_file}")

# Load FRED from silver parquet
print("\n   Loading FRED...")
fred_file = Path("data/silver/fred/date=2025-09/fred_tampa_rent.parquet")
if fred_file.exists():
    df_fred = pd.read_parquet(fred_file)
    print(f"   Found {len(df_fred)} rows in silver parquet")
    print(f"   Columns: {df_fred.columns.tolist()}")
    
    # Map silver columns to RAW schema
    df_load = pd.DataFrame({
        'SERIES_ID': df_fred.get('region_id', 'CUUR0000SEHA'),
        'LABEL': df_fred.get('series_title', 'CPI-U Rent of Primary Residence'),
        'MONTH': pd.to_datetime(df_fred['period']).dt.date,
        'VALUE': df_fred['value'],
        'S3_FILE_PATH': 's3://rent-signals-dev-dd/fred/bronze/date=2025-09/CUUR0000SEHA.json'
    })
    
    success, nchunks, nrows, _ = write_pandas(
        conn, df_load, 'FRED_CPI_LONG', schema='RAW', database='RENTS'
    )
    print(f"   ✅ Loaded {nrows} rows into FRED_CPI_LONG")
else:
    print(f"   ⚠️  Silver file not found: {fred_file}")

# Verify
print("\n5. Verifying data...")
cursor.execute("""
    SELECT 'ZORI_METRO_LONG' as table_name, COUNT(*) as row_count FROM RENTS.RAW.ZORI_METRO_LONG
    UNION ALL
    SELECT 'APTLIST_LONG', COUNT(*) FROM RENTS.RAW.APTLIST_LONG
    UNION ALL
    SELECT 'FRED_CPI_LONG', COUNT(*) FROM RENTS.RAW.FRED_CPI_LONG
""")
counts = cursor.fetchall()
print("\n   Row counts:")
for row in counts:
    print(f"   {row[0]}: {row[1]} rows")

print("\n" + "="*60)
print("✅ SNOWFLAKE SCHEMA FIXED!")
print("="*60)
print("\nNext: Run dbt to verify everything works:")
print("  cd dbt_rent_signals")
print("  dbt run --select staging core marts")
print("  dbt test")

cursor.close()
conn.close()

