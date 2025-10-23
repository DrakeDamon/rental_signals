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
    PaginationMetadata, ErrorResponse, DataSource
)
from .queries import MarketQueries, PriceQueries, RankingQueries, EconomicQueries, RegionalQueries, MetaQueries
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
    allow_methods=["GET", "HEAD"],
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
@app.get("/v1/health", response_model=HealthStatus)
async def health_check():
    """Fast health check for monitoring systems."""
    try:
        db_healthy = await test_database_connection()
        
        return HealthStatus(
            status="healthy" if db_healthy else "degraded",
            timestamp=datetime.utcnow(),
            database="connected" if db_healthy else "disconnected",
            version=settings.api_version
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Market endpoints
@app.get("/v1/markets", response_model=List[MarketSummary])
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
        
        return [MarketSummary(**row) for row in results]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching markets", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch markets")


@app.get("/v1/markets/{metro_slug}/trends", response_model=TrendResponse)
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
        
        # Convert results to trend data points
        trends = [TrendDataPoint(**row) for row in results]
        
        return TrendResponse(
            metro_name=results[0]["METRO_NAME"],
            state_name=results[0]["STATE_NAME"], 
            data_source=data_source,
            trends=trends,
            metadata={
                "months_requested": months,
                "data_source": data_source.value,
                "records_returned": len(results)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching market trends", metro_slug=metro_slug, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch market trends")


@app.get("/v1/markets/compare", response_model=MarketComparisonResponse)
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
        
        markets = [MarketComparisonItem(**row) for row in results]
        
        return MarketComparisonResponse(
            markets=markets,
            comparison_date=results[0]["COMPARISON_DATE"],
            metadata={
                "metros_requested": metro_list,
                "metros_found": len(results)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error comparing markets", metros=metros, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to compare markets")


# Price endpoints
@app.get("/v1/prices/drops", response_model=PriceDropsResponse)
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
        
        # Convert results to price drop objects
        drops = [
            PriceDrop(
                metro_name=row["METRO_NAME"],
                state_name=row["STATE_NAME"],
                current_rent=row["CURRENT_RENT"],
                price_change_pct=row["PRICE_CHANGE_PCT"],
                change_period=timeframe,
                market_temperature=row["MARKET_TEMPERATURE"],
                month_date=row["MONTH_DATE"],
                data_source=DataSource(row["DATA_SOURCE"])
            )
            for row in results
        ]
        
        return PriceDropsResponse(
            drops=drops,
            pagination=PaginationMetadata(
                limit=pagination["limit"],
                offset=pagination["offset"],
                count=len(drops),
                total=total_count,
                has_more=(pagination["offset"] + pagination["limit"]) < total_count,
                next_offset=pagination["offset"] + pagination["limit"] if (pagination["offset"] + pagination["limit"]) < total_count else None
            ),
            filters={
                "threshold": threshold,
                "timeframe": timeframe,
                "state": state
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching price drops", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch price drops")


# Ranking endpoints
@app.get("/v1/rankings/top", response_model=RankingsResponse)
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
        
        rankings = [MarketRanking(**row) for row in results]
        
        return RankingsResponse(
            category=category,
            rankings=rankings,
            pagination=PaginationMetadata(
                limit=pagination["limit"],
                offset=pagination["offset"],
                count=len(rankings),
                total=len(rankings),  # Simplified for top rankings
                has_more=len(rankings) == pagination["limit"],
                next_offset=pagination["offset"] + pagination["limit"] if len(rankings) == pagination["limit"] else None
            ),
            metadata={
                "category": category,
                "description": f"Top markets ranked by {category}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching rankings", category=category, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch rankings")


# Economic endpoints
@app.get("/v1/economics/correlation", response_model=EconomicCorrelationResponse)
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
        
        data = [EconomicCorrelationData(**row) for row in results]
        
        return EconomicCorrelationResponse(
            data=data,
            pagination=PaginationMetadata(
                limit=pagination["limit"],
                offset=pagination["offset"],
                count=len(data),
                total=len(data),  # Simplified for economic data
                has_more=len(data) == pagination["limit"],
                next_offset=pagination["offset"] + pagination["limit"] if len(data) == pagination["limit"] else None
            ),
            metadata={
                "start_year": start_year,
                "description": "Economic correlation analysis between rent and inflation"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching economic correlation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch economic correlation")


# Regional endpoints
@app.get("/v1/regional/summary", response_model=RegionalSummaryResponse)
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
        
        summaries = [RegionalSummary(**row) for row in results]
        
        return RegionalSummaryResponse(
            summaries=summaries,
            pagination=PaginationMetadata(
                limit=pagination["limit"],
                offset=pagination["offset"],
                count=len(summaries),
                total=len(summaries),  # Simplified for regional data
                has_more=len(summaries) == pagination["limit"],
                next_offset=pagination["offset"] + pagination["limit"] if len(summaries) == pagination["limit"] else None
            ),
            metadata={
                "state_filter": state,
                "description": "Regional market summaries and trends"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching regional summary", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch regional summary")


# Metadata endpoints
@app.get("/v1/data/lineage", response_model=DataLineageResponse)
async def get_data_lineage():
    """Get data lineage and quality information for transparency."""
    try:
        query = MetaQueries.get_data_lineage()
        results = await execute_query(query)
        
        lineage = [DataLineageInfo(**row) for row in results]
        
        return DataLineageResponse(
            lineage=lineage,
            metadata={
                "description": "Data lineage and quality monitoring information",
                "tables_monitored": len(lineage)
            }
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


# Root endpoint
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
            "price_drops": "/v1/prices/drops",
            "rankings": "/v1/rankings/top",
            "economic_analysis": "/v1/economics/correlation",
            "regional_summary": "/v1/regional/summary",
            "data_lineage": "/v1/data/lineage"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)