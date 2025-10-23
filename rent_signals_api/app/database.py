"""
Database connection management for Tampa Rent Signals API.
Provides robust Snowflake connectivity with comprehensive error handling.
"""

import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import snowflake.connector
from snowflake.connector import DictCursor
from snowflake.connector.errors import DatabaseError, ProgrammingError
from fastapi import HTTPException
import structlog

from .config import get_snowflake_config

# Set up structured logging
logger = structlog.get_logger(__name__)


class DatabaseError(Exception):
    """Custom database error for API-specific handling."""
    pass


@contextmanager
def get_snowflake_connection():
    """
    Context manager for Snowflake connections with comprehensive error handling.
    
    Yields:
        snowflake.connector.SnowflakeConnection: Active database connection
        
    Raises:
        HTTPException: When database is unavailable or connection fails
    """
    conn = None
    try:
        config = get_snowflake_config()
        logger.info("Attempting Snowflake connection", account=config["account"])
        
        conn = snowflake.connector.connect(**config)
        logger.info("Snowflake connection established successfully")
        yield conn
        
    except DatabaseError as e:
        logger.error("Snowflake database error", error=str(e), error_type="database")
        raise HTTPException(
            status_code=503, 
            detail="Database temporarily unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error("Snowflake programming error", error=str(e), error_type="programming")
        raise HTTPException(
            status_code=500, 
            detail="Database query error. Please contact support."
        )
    except Exception as e:
        logger.error("Unexpected database connection error", error=str(e), error_type="unexpected")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error. Please contact support."
        )
    finally:
        if conn:
            try:
                conn.close()
                logger.info("Snowflake connection closed")
            except Exception as e:
                logger.warning("Error closing Snowflake connection", error=str(e))


async def execute_query(
    query: str, 
    params: Optional[Dict[str, Any]] = None,
    fetch_size: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Execute a SQL query with comprehensive error handling and logging.
    
    Args:
        query: SQL query string with optional parameter placeholders
        params: Dictionary of query parameters
        fetch_size: Optional limit on number of rows to fetch
        
    Returns:
        List of dictionaries representing query results
        
    Raises:
        HTTPException: For database errors or query failures
    """
    # Log query details (truncate for security)
    query_preview = query.replace('\n', ' ').strip()[:100]
    logger.info(
        "Executing database query",
        query_preview=query_preview,
        param_count=len(params or {}),
        fetch_size=fetch_size
    )
    
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor(DictCursor)
            
            # Execute query with parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch results with optional size limit
            if fetch_size:
                results = cursor.fetchmany(fetch_size)
            else:
                results = cursor.fetchall()
            
            # Convert to list of dictionaries for JSON serialization
            result_list = [dict(row) for row in results]
            
            logger.info(
                "Query executed successfully",
                rows_returned=len(result_list),
                execution_time_ms=cursor.sfqid  # Snowflake query ID for tracking
            )
            
            return result_list
            
    except Exception as e:
        logger.error(
            "Query execution failed",
            error=str(e),
            query_preview=query_preview,
            params=params
        )
        # Re-raise to let the context manager handle HTTP exceptions
        raise


async def execute_count_query(query: str, params: Optional[Dict[str, Any]] = None) -> int:
    """
    Execute a COUNT query and return the integer result.
    
    Args:
        query: SQL COUNT query
        params: Optional query parameters
        
    Returns:
        Integer count result
    """
    results = await execute_query(query, params, fetch_size=1)
    if not results:
        return 0
    
    # Get the first value from the first row (COUNT result)
    count_value = list(results[0].values())[0]
    return int(count_value) if count_value is not None else 0


async def test_database_connection() -> bool:
    """
    Test database connectivity for health checks.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        results = await execute_query("SELECT 1 AS test_result", fetch_size=1)
        return len(results) == 1 and results[0].get("TEST_RESULT") == 1
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


# Connection pool configuration (for future optimization)
class ConnectionPool:
    """
    Future enhancement: Connection pooling for better performance.
    Currently using simple connection per request.
    """
    
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self._initialized = False
        
    async def initialize(self):
        """Initialize connection pool (placeholder for future implementation)."""
        self._initialized = True
        logger.info("Connection pool initialized", pool_size=self.pool_size)
        
    async def close(self):
        """Close connection pool (placeholder for future implementation)."""
        self._initialized = False
        logger.info("Connection pool closed")