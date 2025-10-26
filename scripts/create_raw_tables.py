#!/usr/bin/env python3
"""
Create missing RAW tables in Snowflake
"""
import os
import snowflake.connector

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

try:
    print("Creating APTLIST_LONG table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS APTLIST_LONG (
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
    print("✅ APTLIST_LONG created")
    
    print("\nCreating FRED_CPI_LONG table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS FRED_CPI_LONG (
          SERIES_ID VARCHAR(50),
          LABEL VARCHAR(500),
          MONTH DATE,
          VALUE DECIMAL(18, 4),
          LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
          S3_FILE_PATH VARCHAR(500)
        )
    """)
    print("✅ FRED_CPI_LONG created")
    
    print("\nVerifying tables...")
    cursor.execute("SHOW TABLES IN SCHEMA RAW")
    tables = cursor.fetchall()
    print(f"\nTables in RAW schema:")
    for table in tables:
        print(f"  - {table[1]}")
    
    print("\nChecking row counts...")
    cursor.execute("""
        SELECT 'ZORI_METRO_LONG' as table_name, COUNT(*) as row_count FROM RENTS.RAW.ZORI_METRO_LONG
        UNION ALL
        SELECT 'APTLIST_LONG', COUNT(*) FROM RENTS.RAW.APTLIST_LONG
        UNION ALL
        SELECT 'FRED_CPI_LONG', COUNT(*) FROM RENTS.RAW.FRED_CPI_LONG
    """)
    counts = cursor.fetchall()
    print("\nRow counts:")
    for row in counts:
        print(f"  {row[0]}: {row[1]} rows")
    
    print("\n✅ All RAW tables ready!")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()


