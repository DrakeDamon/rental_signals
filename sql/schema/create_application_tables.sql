-- Create APPLICATION schema for user management
-- These are transactional tables, not analytics tables
-- Run this manually in Snowflake before using user management endpoints

USE DATABASE RENTS;
USE WAREHOUSE WH_XS;
USE ROLE ACCOUNTADMIN;

-- Create APPLICATION schema
CREATE SCHEMA IF NOT EXISTS RENTS.APPLICATION;

-- Grant permissions
GRANT USAGE ON SCHEMA RENTS.APPLICATION TO ROLE DBT_ROLE;
GRANT CREATE TABLE ON SCHEMA RENTS.APPLICATION TO ROLE DBT_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA RENTS.APPLICATION TO ROLE DBT_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA RENTS.APPLICATION TO ROLE DBT_ROLE;

-- Users table
CREATE TABLE IF NOT EXISTS RENTS.APPLICATION.USERS (
    user_id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Watchlist table
CREATE TABLE IF NOT EXISTS RENTS.APPLICATION.WATCHLIST (
    watchlist_id VARCHAR PRIMARY KEY DEFAULT UUID_STRING(),
    user_id VARCHAR NOT NULL,
    location_business_key VARCHAR NOT NULL,
    metro_slug VARCHAR,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    notes VARCHAR(500),
    FOREIGN KEY (user_id) REFERENCES RENTS.APPLICATION.USERS(user_id),
    UNIQUE (user_id, location_business_key)
);

-- Price alerts table
CREATE TABLE IF NOT EXISTS RENTS.APPLICATION.PRICE_ALERTS (
    alert_id VARCHAR PRIMARY KEY DEFAULT UUID_STRING(),
    user_id VARCHAR NOT NULL,
    location_business_key VARCHAR NOT NULL,
    metro_slug VARCHAR,
    alert_type VARCHAR NOT NULL,  -- 'price_drop', 'threshold', 'trend'
    threshold_value DECIMAL(10,2),
    channel VARCHAR DEFAULT 'email',  -- 'email', 'sms'
    cadence VARCHAR DEFAULT 'daily',  -- 'immediate', 'daily', 'weekly'
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    last_triggered_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES RENTS.APPLICATION.USERS(user_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON RENTS.APPLICATION.WATCHLIST(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_location ON RENTS.APPLICATION.WATCHLIST(location_business_key);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON RENTS.APPLICATION.PRICE_ALERTS(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_location ON RENTS.APPLICATION.PRICE_ALERTS(location_business_key);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON RENTS.APPLICATION.PRICE_ALERTS(active, user_id);

-- Verify tables created
SELECT 'Users table created' as status, COUNT(*) as row_count FROM RENTS.APPLICATION.USERS;
SELECT 'Watchlist table created' as status, COUNT(*) as row_count FROM RENTS.APPLICATION.WATCHLIST;
SELECT 'Price alerts table created' as status, COUNT(*) as row_count FROM RENTS.APPLICATION.PRICE_ALERTS;

