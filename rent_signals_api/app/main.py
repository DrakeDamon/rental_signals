"""
Tampa Rent Signals RESTful API
FastAPI application providing rental market data analysis and price tracking.
"""

import logging
import time
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from .config import get_settings
from .database import execute_query, execute_count_query, test_database_connection
from .models import (
    HealthStatus, MarketSummary, TrendResponse, TrendDataPoint,
    PriceDropsResponse, PriceDrop, RankingsResponse, MarketRanking,
    EconomicCorrelationResponse, EconomicCorrelationData,
    RegionalSummaryResponse, RegionalSummary,
    DataLineageResponse, DataLineageInfo,
    MarketComparisonResponse, MarketComparisonItem,
    PaginationMetadata, ErrorResponse, DataSource,
    # New standardized response models
    StandardAPIResponse, APIMetadata, APIPagination,
    # User management models
    WatchlistItemCreate, WatchlistItem, AlertCreate, AlertUpdate, Alert
)
from .queries import (
    MarketQueries, PriceQueries, RankingQueries, EconomicQueries, 
    RegionalQueries, MetaQueries, UserQueries
)
from .utils import normalize_metro_slug, normalize_state_name, paginate_results, sanitize_query_param

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Get application settings
settings = get_settings()

# Initialize FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=round(process_time, 3),
        user_agent=request.headers.get("user-agent"),
        client_ip=request.client.host
    )
    
    return response


# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail,
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured error responses."""
    logger.error(
        "Unexpected error occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="Internal server error occurred",
            details={"error_type": type(exc).__name__}
        ).dict()
    )


# Dependency for pagination validation
def validate_pagination(
    limit: int = Query(20, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Starting position")
) -> Dict[str, int]:
    """Validate and return pagination parameters."""
    return {"limit": limit, "offset": offset}


# Health check endpoints
@app.head("/v1/health")
@app.get("/v1/health")
async def health_check():
    """Fast health check for monitoring systems."""
    try:
        db_healthy = await test_database_connection()
        
        health_data = {
            "status": "healthy" if db_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected" if db_healthy else "disconnected",
            "version": settings.api_version
        }
        
        return StandardAPIResponse(
            success=db_healthy,
            data=health_data,
            metadata=APIMetadata(
                total_count=1,
                returned_count=1,
                data_freshness=datetime.utcnow(),
                sources=["Snowflake"],
                quality_score=10.0 if db_healthy else 0.0
            )
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Market endpoints
@app.get("/v1/markets")
async def get_markets(
    state: Optional[str] = Query(None, description="Filter by state name"),
    pagination: Dict[str, int] = Depends(validate_pagination)
):
    """Get summary of all available rental markets."""
    try:
        # Normalize state filter if provided
        state_filter = normalize_state_name(state).lower() if state else None
        
        query = MarketQueries.get_markets_summary(
            state_filter=state_filter,
            limit=pagination["limit"],
            offset=pagination["offset"]
        )
        
        query_params = {
            "limit": pagination["limit"],
            "offset": pagination["offset"]
        }
        
        if state_filter:
            query_params["state_filter"] = state_filter
        
        results = await execute_query(query, query_params)
        
        # Get total count for pagination
        total_count = len(results) if len(results) < pagination["limit"] else pagination["offset"] + len(results) + 1
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=total_count,
                returned_count=len(results),
                data_freshness=results[0].get('LAST_UPDATED') if results else None,
                sources=['Zillow ZORI', 'ApartmentList'],
                quality_score=None
            ),
            pagination=APIPagination(
                limit=pagination["limit"],
                offset=pagination["offset"],
                has_more=len(results) == pagination["limit"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching markets", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch markets")


@app.get("/v1/markets/{metro_slug}/trends")
async def get_market_trends(
    metro_slug: str,
    months: int = Query(12, ge=1, le=60, description="Number of months of historical data"),
    data_source: DataSource = Query(DataSource.ZILLOW_ZORI, description="Data source")
):
    """Get historical rent trends for a specific metro area."""
    try:
        # Normalize metro slug for database lookup
        normalized_slug = normalize_metro_slug(sanitize_query_param(metro_slug))
        
        query = MarketQueries.get_market_trends(
            metro_slug=normalized_slug,
            data_source=data_source.value,
            months=months
        )
        
        results = await execute_query(query, {
            "metro_slug": normalized_slug,
            "data_source": data_source.value,
            "months": months
        })
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for metro: {metro_slug}"
            )
        
        # Build response data
        trend_data = {
            "metro_name": results[0]["METRO_NAME"],
            "state_name": results[0]["STATE_NAME"],
            "data_source": data_source.value,
            "trends": results,
            "months_requested": months
        }
        
        return StandardAPIResponse(
            success=True,
            data=trend_data,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=results[-1].get('MONTH_DATE') if results else None,
                sources=[data_source.value],
                quality_score=None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching market trends", metro_slug=metro_slug, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch market trends")


@app.get("/v1/markets/compare")
async def compare_markets(
    metros: str = Query(..., description="Comma-separated list of metro slugs to compare")
):
    """Compare multiple rental markets side-by-side."""
    try:
        # Parse and normalize metro slugs
        metro_list = [normalize_metro_slug(sanitize_query_param(m.strip())) for m in metros.split(",")]
        metro_list = [m for m in metro_list if m]  # Remove empty strings
        
        if not metro_list:
            raise HTTPException(status_code=400, detail="No valid metro areas specified")
        
        if len(metro_list) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 metro areas allowed for comparison")
        
        query = MarketQueries.get_market_comparison(metro_list)
        
        # Build query parameters for metro slugs
        query_params = {f"metro_slug_{i}": slug for i, slug in enumerate(metro_list)}
        
        results = await execute_query(query, query_params)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No data found for the specified metro areas"
            )
        
        comparison_data = {
            "markets": results,
            "comparison_date": results[0]["COMPARISON_DATE"],
            "metros_requested": metro_list,
            "metros_found": len(results)
        }
        
        return StandardAPIResponse(
            success=True,
            data=comparison_data,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=results[0].get("COMPARISON_DATE"),
                sources=['Zillow ZORI'],
                quality_score=None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error comparing markets", metros=metros, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to compare markets")


# Price endpoints
@app.get("/v1/prices/drops")
async def get_price_drops(
    threshold: float = Query(5.0, ge=0.1, le=50.0, description="Minimum price drop percentage"),
    timeframe: str = Query("month", regex="^(week|month|quarter)$", description="Time period for price change"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    pagination: Dict[str, int] = Depends(validate_pagination)
):
    """Get markets with recent significant price drops."""
    try:
        # Normalize state filter if provided
        state_filter = normalize_state_name(state).lower() if state else None
        
        # Get price drops
        query = PriceQueries.get_price_drops(
            threshold=threshold,
            timeframe=timeframe,
            state_filter=state_filter,
            limit=pagination["limit"],
            offset=pagination["offset"]
        )
        
        query_params = {
            "threshold": threshold,
            "limit": pagination["limit"],
            "offset": pagination["offset"]
        }
        
        if state_filter:
            query_params["state_filter"] = state_filter
        
        results = await execute_query(query, query_params)
        
        # Get total count for pagination
        count_query = PriceQueries.count_price_drops(
            threshold=threshold,
            timeframe=timeframe,
            state_filter=state_filter
        )
        
        count_params = {"threshold": threshold}
        if state_filter:
            count_params["state_filter"] = state_filter
        
        total_count = await execute_count_query(count_query, count_params)
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=total_count,
                returned_count=len(results),
                data_freshness=results[0].get('MONTH_DATE') if results else None,
                sources=['Zillow ZORI'],
                quality_score=None
            ),
            pagination=APIPagination(
                limit=pagination["limit"],
                offset=pagination["offset"],
                has_more=(pagination["offset"] + pagination["limit"]) < total_count
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching price drops", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch price drops")


# Ranking endpoints
@app.get("/v1/rankings/top")
async def get_top_rankings(
    category: str = Query("growth", regex="^(growth|rent|heat_score|investment)$", description="Ranking category"),
    pagination: Dict[str, int] = Depends(validate_pagination)
):
    """Get top market rankings by category."""
    try:
        query = RankingQueries.get_top_rankings(
            category=category,
            limit=pagination["limit"],
            offset=pagination["offset"]
        )
        
        results = await execute_query(query, {
            "limit": pagination["limit"],
            "offset": pagination["offset"]
        })
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=results[0].get('MONTH_DATE') if results else None,
                sources=['Zillow ZORI'],
                quality_score=None
            ),
            pagination=APIPagination(
                limit=pagination["limit"],
                offset=pagination["offset"],
                has_more=len(results) == pagination["limit"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching rankings", category=category, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch rankings")


# Economic endpoints
@app.get("/v1/economics/correlation")
async def get_economic_correlation(
    start_year: Optional[int] = Query(None, ge=2000, le=2030, description="Starting year for analysis"),
    pagination: Dict[str, int] = Depends(validate_pagination)
):
    """Get rent vs inflation correlation analysis with policy implications."""
    try:
        query = EconomicQueries.get_economic_correlation(
            start_year=start_year,
            limit=pagination["limit"],
            offset=pagination["offset"]
        )
        
        query_params = {
            "limit": pagination["limit"],
            "offset": pagination["offset"]
        }
        
        if start_year:
            query_params["start_year"] = start_year
        
        results = await execute_query(query, query_params)
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=results[0].get('MONTH_DATE') if results else None,
                sources=['Zillow ZORI', 'FRED'],
                quality_score=None
            ),
            pagination=APIPagination(
                limit=pagination["limit"],
                offset=pagination["offset"],
                has_more=len(results) == pagination["limit"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching economic correlation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch economic correlation")


# Regional endpoints
@app.get("/v1/regional/summary")
async def get_regional_summary(
    state: Optional[str] = Query(None, description="Filter by state name"),
    pagination: Dict[str, int] = Depends(validate_pagination)
):
    """Get state and regional market aggregations."""
    try:
        # Normalize state filter if provided
        state_filter = normalize_state_name(state).lower() if state else None
        
        query = RegionalQueries.get_regional_summary(
            state_filter=state_filter,
            limit=pagination["limit"],
            offset=pagination["offset"]
        )
        
        query_params = {
            "limit": pagination["limit"],
            "offset": pagination["offset"]
        }
        
        if state_filter:
            query_params["state_filter"] = state_filter
        
        results = await execute_query(query, query_params)
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=datetime.utcnow(),
                sources=['Zillow ZORI', 'ApartmentList'],
                quality_score=None
            ),
            pagination=APIPagination(
                limit=pagination["limit"],
                offset=pagination["offset"],
                has_more=len(results) == pagination["limit"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching regional summary", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch regional summary")


# Metadata endpoints
@app.get("/v1/data/lineage")
async def get_data_lineage():
    """Get data lineage and quality information for transparency."""
    try:
        query = MetaQueries.get_data_lineage()
        results = await execute_query(query)
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=results[0].get('LAST_UPDATED') if results else None,
                sources=['Zillow ZORI', 'ApartmentList', 'FRED'],
                quality_score=sum(r.get('OVERALL_RELIABILITY_SCORE', 0) for r in results) / len(results) if results else None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching data lineage", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch data lineage")


@app.get("/v1/meta/schema")
async def get_schema_info():
    """Get database schema information for developers."""
    try:
        query = MetaQueries.get_schema_info()
        results = await execute_query(query)
        
        return {
            "schema_info": results,
            "metadata": {
                "description": "Database schema information for API developers",
                "tables_documented": len(set(row["TABLE_NAME"] for row in results))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching schema info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch schema information")


# ============================================================================
# NEW ENDPOINTS - Individual Market Details
# ============================================================================

@app.get("/v1/markets/{metro_slug}")
async def get_market_details(metro_slug: str):
    """Get detailed information for a specific market by slug."""
    try:
        query = MarketQueries.get_market_by_slug(metro_slug)
        results = execute_query(query)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Market not found: {metro_slug}")
        
        market_data = results[0]
        
        return StandardAPIResponse(
            success=True,
            data=market_data,
            metadata=APIMetadata(
                total_count=1,
                returned_count=1,
                data_freshness=market_data.get('LAST_UPDATED'),
                sources=[market_data.get('DATA_SOURCE', 'Zillow ZORI')],
                quality_score=market_data.get('DATA_QUALITY_SCORE')
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching market details", metro_slug=metro_slug, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch market details")


@app.get("/v1/prices/featured")
async def get_featured_markets(limit: int = Query(10, ge=1, le=50)):
    """Get top featured markets by heat score and growth."""
    try:
        query = PriceQueries.get_featured_markets(limit=limit)
        results = execute_query(query)
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=results[0].get('LAST_UPDATED') if results else None,
                sources=['Zillow ZORI', 'ApartmentList'],
                quality_score=None
            )
        )
        
    except Exception as e:
        logger.error("Error fetching featured markets", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch featured markets")


@app.get("/v1/rankings/state/{state}")
async def get_state_rankings(state: str, limit: int = Query(50, ge=1, le=100)):
    """Get market rankings for a specific state."""
    try:
        query = RankingQueries.get_state_rankings(state=state, limit=limit)
        results = execute_query(query)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No markets found for state: {state}")
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=results[0].get('LAST_UPDATED') if results else None,
                sources=['Zillow ZORI'],
                quality_score=None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching state rankings", state=state, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch state rankings")


@app.get("/v1/analytics/heat-map")
async def get_heat_map_data():
    """Get market heat scores with geographic coordinates for map visualization."""
    try:
        query = RankingQueries.get_heat_map_data()
        results = execute_query(query)
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=results[0].get('LAST_UPDATED') if results else None,
                sources=['Zillow ZORI', 'ApartmentList'],
                quality_score=None
            )
        )
        
    except Exception as e:
        logger.error("Error fetching heat map data", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch heat map data")


@app.get("/v1/data/freshness")
async def get_data_freshness():
    """Get data freshness status by source."""
    try:
        query = MetaQueries.get_freshness_by_source()
        results = execute_query(query)
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=datetime.utcnow(),
                sources=[r.get('SOURCE_NAME') for r in results],
                quality_score=None
            )
        )
        
    except Exception as e:
        logger.error("Error fetching data freshness", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch data freshness")


# ============================================================================
# USER MANAGEMENT ENDPOINTS - Watchlist
# ============================================================================

@app.post("/v1/watchlist")
async def add_to_watchlist(item: WatchlistItemCreate):
    """Add a market to user's watchlist."""
    try:
        # Lookup location_business_key from metro_slug
        lookup_query = UserQueries.lookup_location_key(item.metro_slug)
        location_results = execute_query(lookup_query)
        
        if not location_results:
            raise HTTPException(status_code=404, detail=f"Market not found: {item.metro_slug}")
        
        location_key = location_results[0]['LOCATION_BUSINESS_KEY']
        
        # Add to watchlist
        insert_query = UserQueries.add_to_watchlist(
            user_id=item.user_id,
            location_business_key=location_key,
            metro_slug=item.metro_slug
        )
        execute_query(insert_query)
        
        return StandardAPIResponse(
            success=True,
            data={"message": "Added to watchlist successfully", "metro_slug": item.metro_slug},
            metadata=APIMetadata(
                total_count=1,
                returned_count=1,
                data_freshness=datetime.utcnow(),
                sources=[],
                quality_score=None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding to watchlist", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to add to watchlist")


@app.get("/v1/watchlist")
async def get_watchlist(user_id: str = Query(..., description="User ID")):
    """Get user's watchlist with current market data."""
    try:
        query = UserQueries.get_watchlist(user_id=user_id)
        results = execute_query(query)
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=datetime.utcnow(),
                sources=['Zillow ZORI'],
                quality_score=None
            )
        )
        
    except Exception as e:
        logger.error("Error fetching watchlist", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")


@app.delete("/v1/watchlist/{watchlist_id}")
async def remove_from_watchlist(watchlist_id: str):
    """Remove item from watchlist."""
    try:
        query = UserQueries.remove_from_watchlist(watchlist_id=watchlist_id)
        execute_query(query)
        
        return StandardAPIResponse(
            success=True,
            data={"message": "Removed from watchlist successfully"},
            metadata=APIMetadata(
                total_count=1,
                returned_count=1,
                data_freshness=datetime.utcnow(),
                sources=[],
                quality_score=None
            )
        )
        
    except Exception as e:
        logger.error("Error removing from watchlist", watchlist_id=watchlist_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to remove from watchlist")


# ============================================================================
# USER MANAGEMENT ENDPOINTS - Alerts
# ============================================================================

@app.post("/v1/alerts")
async def create_alert(alert: AlertCreate):
    """Create a price alert for a market."""
    try:
        # Lookup location_business_key
        lookup_query = UserQueries.lookup_location_key(alert.metro_slug)
        location_results = execute_query(lookup_query)
        
        if not location_results:
            raise HTTPException(status_code=404, detail=f"Market not found: {alert.metro_slug}")
        
        location_key = location_results[0]['LOCATION_BUSINESS_KEY']
        
        # Create alert
        insert_query = UserQueries.create_alert(
            user_id=alert.user_id,
            location_business_key=location_key,
            metro_slug=alert.metro_slug,
            alert_type=alert.alert_type,
            threshold_value=alert.threshold_value,
            channel=alert.channel,
            cadence=alert.cadence
        )
        execute_query(insert_query)
        
        return StandardAPIResponse(
            success=True,
            data={"message": "Alert created successfully", "metro_slug": alert.metro_slug},
            metadata=APIMetadata(
                total_count=1,
                returned_count=1,
                data_freshness=datetime.utcnow(),
                sources=[],
                quality_score=None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating alert", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create alert")


@app.get("/v1/alerts")
async def get_alerts(user_id: str = Query(..., description="User ID")):
    """Get user's active alerts."""
    try:
        query = UserQueries.get_alerts(user_id=user_id)
        results = execute_query(query)
        
        return StandardAPIResponse(
            success=True,
            data=results,
            metadata=APIMetadata(
                total_count=len(results),
                returned_count=len(results),
                data_freshness=datetime.utcnow(),
                sources=[],
                quality_score=None
            )
        )
        
    except Exception as e:
        logger.error("Error fetching alerts", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")


@app.put("/v1/alerts/{alert_id}")
async def update_alert(alert_id: str, update: AlertUpdate):
    """Update alert configuration."""
    try:
        updates = update.dict(exclude_unset=True)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        query = UserQueries.update_alert(alert_id=alert_id, updates=updates)
        if query:
            execute_query(query)
        
        return StandardAPIResponse(
            success=True,
            data={"message": "Alert updated successfully", "alert_id": alert_id},
            metadata=APIMetadata(
                total_count=1,
                returned_count=1,
                data_freshness=datetime.utcnow(),
                sources=[],
                quality_score=None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update alert")


@app.delete("/v1/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert."""
    try:
        query = UserQueries.delete_alert(alert_id=alert_id)
        execute_query(query)
        
        return StandardAPIResponse(
            success=True,
            data={"message": "Alert deleted successfully"},
            metadata=APIMetadata(
                total_count=1,
                returned_count=1,
                data_freshness=datetime.utcnow(),
                sources=[],
                quality_score=None
            )
        )
        
    except Exception as e:
        logger.error("Error deleting alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete alert")


# ============================================================================
# Root endpoint
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "title": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs_url": "/docs",
        "health_check": "/v1/health",
        "endpoints": {
            "markets": "/v1/markets",
            "market_details": "/v1/markets/{metro_slug}",
            "featured_markets": "/v1/prices/featured",
            "price_drops": "/v1/prices/drops",
            "rankings": "/v1/rankings/top",
            "state_rankings": "/v1/rankings/state/{state}",
            "heat_map": "/v1/analytics/heat-map",
            "economic_analysis": "/v1/economics/correlation",
            "regional_summary": "/v1/regional/summary",
            "data_lineage": "/v1/data/lineage",
            "data_freshness": "/v1/data/freshness",
            "watchlist": "/v1/watchlist",
            "alerts": "/v1/alerts"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)