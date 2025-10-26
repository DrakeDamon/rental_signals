#!/usr/bin/env python3
"""
Reset Snowflake RAW tables to match the correct schema
"""
import snowflake.connector

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
print("RESETTING SNOWFLAKE RAW SCHEMA")
print("="*60)

# Drop wrong tables
print("\n1. Dropping tables with incorrect schema...")
cursor.execute("DROP TABLE IF EXISTS RENTS.RAW.APTLIST_LONG CASCADE")
print("   ✅ Dropped APTLIST_LONG")

cursor.execute("DROP TABLE IF EXISTS RENTS.RAW.FRED_CPI_LONG CASCADE")
print("   ✅ Dropped FRED_CPI_LONG")

# Create with correct schema (matching load_from_s3_bronze.sql)
print("\n2. Creating tables with correct schema...")

cursor.execute("""
    CREATE TABLE RENTS.RAW.APTLIST_LONG (
      LOCATION_FIPS_CODE VARCHAR(20),
      REGIONID VARCHAR(50),
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
print("   ✅ Created APTLIST_LONG")

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
print("   ✅ Created FRED_CPI_LONG")

# Add clustering
print("\n3. Adding clustering...")
cursor.execute("ALTER TABLE RENTS.RAW.APTLIST_LONG CLUSTER BY (MONTH, LOCATION_NAME)")
cursor.execute("ALTER TABLE RENTS.RAW.FRED_CPI_LONG CLUSTER BY (SERIES_ID, MONTH)")
print("   ✅ Clustering added")

# Verify structure
print("\n4. Verifying table structure...")
for table in ['APTLIST_LONG', 'FRED_CPI_LONG']:
    cursor.execute(f"DESC TABLE {table}")
    cols = cursor.fetchall()
    print(f"\n   {table} columns:")
    for col in cols:
        print(f"     - {col[0]} ({col[1]})")

print("\n" + "="*60)
print("✅ SNOWFLAKE RAW SCHEMA RESET!")
print("="*60)
print("\nTables are ready but empty.")
print("Next: Load data from S3 bronze or local files")

cursor.close()
conn.close()

