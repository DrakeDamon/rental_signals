#!/usr/bin/env python3
"""
Check actual column names in Snowflake RAW tables
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

tables = ['ZORI_METRO_LONG', 'APTLIST_LONG', 'FRED_CPI_LONG']

for table in tables:
    print(f"\n{'='*60}")
    print(f"Table: {table}")
    print('='*60)
    cursor.execute(f"DESC TABLE {table}")
    columns = cursor.fetchall()
    print(f"\nColumns:")
    for col in columns:
        print(f"  - {col[0]} ({col[1]})")
    
    # Show sample data
    print(f"\nSample row:")
    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
    row = cursor.fetchone()
    if row:
        col_names = [desc[0] for desc in cursor.description]
        for i, val in enumerate(row):
            print(f"  {col_names[i]}: {val}")
    else:
        print("  (no data)")

cursor.close()
conn.close()


