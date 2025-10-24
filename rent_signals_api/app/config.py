"""
Configuration management for Tampa Rent Signals API.
Uses Pydantic Settings for type-safe environment variable handling.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Snowflake Database Configuration
    snowflake_account: str = Field(..., description="Snowflake account identifier")
    snowflake_user: str = Field(..., description="Snowflake username")
    snowflake_password: str = Field(..., description="Snowflake password")
    snowflake_database: str = Field(default="RENTS", description="Snowflake database name")
    snowflake_warehouse: str = Field(default="WH_XS", description="Snowflake warehouse")
    snowflake_role: str = Field(default="ACCOUNTADMIN", description="Snowflake role")
    
    # API Configuration
    api_title: str = Field(default="Tampa Rent Signals API", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    api_description: str = Field(
        default="RESTful API for Tampa rental market data analysis and price tracking",
        description="API description"
    )
    
    # Query and Performance Settings
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    max_query_limit: int = Field(default=100, description="Maximum query result limit")
    default_query_limit: int = Field(default=20, description="Default query result limit")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    # Environment Settings
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Optional: Redis Configuration (for future caching)
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")
    
    # Pydantic v2 settings configuration
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Convenience function for accessing settings
def get_snowflake_config() -> dict:
    """Get Snowflake connection configuration as a dictionary."""
    settings = get_settings()
    return {
        "account": settings.snowflake_account,
        "user": settings.snowflake_user,
        "password": settings.snowflake_password,
        "database": settings.snowflake_database,
        "warehouse": settings.snowflake_warehouse,
        "role": settings.snowflake_role,
    }