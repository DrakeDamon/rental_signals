#!/usr/bin/env python3
"""
Create missing SNAPSHOTS schema in Snowflake for dbt SCD2 snapshots
"""
import snowflake.connector

conn = snowflake.connector.connect(
    account='mvc20409.us-east-1',
    user='DRAKEDAMON',
    password='SnowflakeFreedom2027!',
    database='RENTS',
    warehouse='WH_XS',
    role='ACCOUNTADMIN'
)

cursor = conn.cursor()

print("Creating SNAPSHOTS schema...")
cursor.execute("CREATE SCHEMA IF NOT EXISTS RENTS.SNAPSHOTS")
print("✅ SNAPSHOTS schema created")

print("\nGranting permissions...")
cursor.execute("GRANT USAGE ON SCHEMA RENTS.SNAPSHOTS TO ROLE DBT_ROLE")
cursor.execute("GRANT ALL ON SCHEMA RENTS.SNAPSHOTS TO ROLE DBT_ROLE")
cursor.execute("GRANT ALL ON FUTURE TABLES IN SCHEMA RENTS.SNAPSHOTS TO ROLE DBT_ROLE")
print("✅ Permissions granted")

cursor.close()
conn.close()

print("\n✅ SNAPSHOTS schema ready!")


