"""
Pydantic models for Tampa Rent Signals API responses.
Defines data structures for type-safe API responses and validation.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any, Union, Generic, TypeVar
from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel
from enum import Enum


# Generic type for data payload
T = TypeVar('T')


class APIMetadata(BaseModel):
    """Metadata for standardized API responses."""
    total_count: int = Field(..., description="Total number of items available")
    returned_count: int = Field(..., description="Number of items returned in this response")
    data_freshness: Optional[datetime] = Field(None, description="Timestamp of most recent data")
    sources: List[str] = Field(..., description="Data sources used in response")
    quality_score: Optional[float] = Field(None, description="Average data quality score (1-10)")


class APIPagination(BaseModel):
    """Pagination information for standardized API responses."""
    limit: int = Field(..., description="Maximum number of items per page")
    offset: int = Field(..., description="Starting position in result set")
    has_more: bool = Field(..., description="Whether more results are available")


class StandardAPIResponse(GenericModel, Generic[T]):
    """Standardized API response wrapper for all endpoints."""
    success: bool = Field(True, description="Whether the request was successful")
    data: T = Field(..., description="Response data payload")
    metadata: APIMetadata = Field(..., description="Response metadata")
    pagination: Optional[APIPagination] = Field(None, description="Pagination information (if applicable)")


class DataSource(str, Enum):
    """Enumeration of available data sources."""
    ZILLOW_ZORI = "Zillow ZORI"
    APARTMENTLIST = "ApartmentList"


class MarketTemperature(str, Enum):
    """Market temperature classifications."""
    VERY_HOT = "Very Hot"
    HOT = "Hot"
    WARM = "Warm"
    COOL = "Cool"
    COLD = "Cold"
    UNKNOWN = "Unknown"


class MarketSizeCategory(str, Enum):
    """Market size categories."""
    MAJOR_METRO = "Major Metro (5M+)"
    LARGE_METRO = "Large Metro (1M-5M)"
    MEDIUM_METRO = "Medium Metro (250K-1M)"
    SMALL_METRO = "Small Metro (<250K)"


class PaginationMetadata(BaseModel):
    """Pagination metadata for API responses."""
    limit: int = Field(..., description="Number of results per page")
    offset: int = Field(..., description="Starting position")
    count: int = Field(..., description="Number of results in current page")
    total: int = Field(..., description="Total number of available results")
    has_more: bool = Field(..., description="Whether more results are available")
    next_offset: Optional[int] = Field(None, description="Offset for next page")


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    database: str = Field(..., description="Database connectivity status")
    version: str = Field(..., description="API version")


class MarketSummary(BaseModel):
    """Summary information for a rental market."""
    metro_id: str = Field(..., description="Location business key (unique identifier)")
    metro_slug: Optional[str] = Field(None, description="URL-friendly metro slug")
    metro_name: str = Field(..., description="Metro area name")
    state_name: str = Field(..., description="State name")
    current_rent: Optional[float] = Field(None, description="Current average rent")
    yoy_pct_change: Optional[float] = Field(None, description="Year-over-year percentage change")
    mom_pct_change: Optional[float] = Field(None, description="Month-over-month percentage change")
    market_temperature: Optional[MarketTemperature] = Field(None, description="Market temperature classification")
    market_size_category: Optional[MarketSizeCategory] = Field(None, description="Market size category")
    population: Optional[int] = Field(None, description="Metro area population")
    data_source: DataSource = Field(..., description="Data source")
    lat: Optional[float] = Field(None, description="Latitude coordinate for map display")
    lng: Optional[float] = Field(None, description="Longitude coordinate for map display")
    last_updated: Optional[date] = Field(None, description="Date of most recent data")
    
    @validator('current_rent', 'yoy_pct_change', 'mom_pct_change', 'lat', 'lng')
    def round_floats(cls, v):
        """Round float values to appropriate decimal places."""
        if v is None:
            return None
        # Round lat/lng to 4 decimals, currency to 2
        return round(v, 4) if isinstance(v, float) and abs(v) < 200 else round(v, 2)


class TrendDataPoint(BaseModel):
    """Single data point in a trend series."""
    month_date: date = Field(..., description="Month date")
    rent_value: Optional[float] = Field(None, description="Rent value for the month")
    yoy_pct_change: Optional[float] = Field(None, description="Year-over-year percentage change")
    mom_pct_change: Optional[float] = Field(None, description="Month-over-month percentage change")
    market_temperature: Optional[MarketTemperature] = Field(None, description="Market temperature")
    
    @validator('rent_value', 'yoy_pct_change', 'mom_pct_change')
    def round_floats(cls, v):
        return round(v, 2) if v is not None else None


class TrendResponse(BaseModel):
    """Response model for market trend data."""
    metro_name: str = Field(..., description="Metro area name")
    state_name: str = Field(..., description="State name")
    data_source: DataSource = Field(..., description="Data source")
    trends: List[TrendDataPoint] = Field(..., description="Historical trend data")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


class PriceDrop(BaseModel):
    """Model for price drop information."""
    metro_name: str = Field(..., description="Metro area name")
    state_name: str = Field(..., description="State name")
    current_rent: Optional[float] = Field(None, description="Current rent value")
    price_change_pct: float = Field(..., description="Price change percentage")
    change_period: str = Field(..., description="Time period for the change")
    market_temperature: Optional[MarketTemperature] = Field(None, description="Market temperature")
    month_date: date = Field(..., description="Month of the data")
    data_source: DataSource = Field(..., description="Data source")
    
    @validator('current_rent', 'price_change_pct')
    def round_floats(cls, v):
        return round(v, 2) if v is not None else None


class PriceDropsResponse(BaseModel):
    """Response model for price drops endpoint."""
    drops: List[PriceDrop] = Field(..., description="List of price drops")
    pagination: PaginationMetadata = Field(..., description="Pagination information")
    filters: Dict[str, Any] = Field(..., description="Applied filters")


class MarketRanking(BaseModel):
    """Model for market ranking information."""
    metro_name: str = Field(..., description="Metro area name")
    state_name: str = Field(..., description="State name")
    market_size_category: Optional[MarketSizeCategory] = Field(None, description="Market size category")
    rank: int = Field(..., description="Rank for the specified category")
    score: float = Field(..., description="Score for the ranking category")
    metric_value: Optional[float] = Field(None, description="Value of the metric being ranked")
    population: Optional[int] = Field(None, description="Metro area population")
    
    @validator('score', 'metric_value')
    def round_floats(cls, v):
        return round(v, 2) if v is not None else None


class RankingsResponse(BaseModel):
    """Response model for market rankings."""
    category: str = Field(..., description="Ranking category")
    rankings: List[MarketRanking] = Field(..., description="Market rankings")
    pagination: PaginationMetadata = Field(..., description="Pagination information")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


class EconomicCorrelationData(BaseModel):
    """Model for economic correlation data."""
    year: int = Field(..., description="Year")
    quarter: int = Field(..., description="Quarter")
    economic_regime: Optional[str] = Field(None, description="Economic regime classification")
    rent_cpi_correlation: Optional[float] = Field(None, description="Rent vs CPI correlation")
    affordability_pressure: Optional[str] = Field(None, description="Affordability pressure level")
    policy_implications: Optional[str] = Field(None, description="Policy implications")
    rent_housing_cpi_spread: Optional[float] = Field(None, description="Rent vs housing CPI spread")
    
    @validator('rent_cpi_correlation', 'rent_housing_cpi_spread')
    def round_floats(cls, v):
        return round(v, 4) if v is not None else None


class EconomicCorrelationResponse(BaseModel):
    """Response model for economic correlation data."""
    data: List[EconomicCorrelationData] = Field(..., description="Economic correlation data")
    pagination: PaginationMetadata = Field(..., description="Pagination information")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


class RegionalSummary(BaseModel):
    """Model for regional market summary."""
    state_name: str = Field(..., description="State name")
    region_name: Optional[str] = Field(None, description="Region name")
    metro_count: int = Field(..., description="Number of metro areas")
    avg_rent_index: Optional[float] = Field(None, description="Average rent index")
    weighted_yoy_growth: Optional[float] = Field(None, description="Population-weighted YoY growth")
    dominant_trend: Optional[str] = Field(None, description="Dominant market trend")
    total_population: Optional[int] = Field(None, description="Total population")
    market_concentration: Optional[float] = Field(None, description="Market concentration index")
    
    @validator('avg_rent_index', 'weighted_yoy_growth', 'market_concentration')
    def round_floats(cls, v):
        return round(v, 2) if v is not None else None


class RegionalSummaryResponse(BaseModel):
    """Response model for regional summary data."""
    summaries: List[RegionalSummary] = Field(..., description="Regional summaries")
    pagination: PaginationMetadata = Field(..., description="Pagination information")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


class DataLineageInfo(BaseModel):
    """Model for data lineage and quality information."""
    table_name: str = Field(..., description="Table name")
    layer: str = Field(..., description="Data layer (staging, core, marts)")
    source_name: str = Field(..., description="Data source name")
    data_freshness_status: str = Field(..., description="Data freshness status")
    data_quality_status: str = Field(..., description="Data quality status")
    overall_reliability_score: int = Field(..., description="Overall reliability score")
    days_since_latest_data: int = Field(..., description="Days since latest data")
    last_updated: datetime = Field(..., description="Last update timestamp")


class DataLineageResponse(BaseModel):
    """Response model for data lineage information."""
    lineage: List[DataLineageInfo] = Field(..., description="Data lineage information")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


class MarketComparisonItem(BaseModel):
    """Model for market comparison data."""
    metro_name: str = Field(..., description="Metro area name")
    state_name: str = Field(..., description="State name")
    current_rent: Optional[float] = Field(None, description="Current rent value")
    yoy_pct_change: Optional[float] = Field(None, description="Year-over-year change")
    mom_pct_change: Optional[float] = Field(None, description="Month-over-month change")
    market_temperature: Optional[MarketTemperature] = Field(None, description="Market temperature")
    population: Optional[int] = Field(None, description="Population")
    rank_rent: Optional[int] = Field(None, description="Rent ranking")
    rank_growth: Optional[int] = Field(None, description="Growth ranking")
    
    @validator('current_rent', 'yoy_pct_change', 'mom_pct_change')
    def round_floats(cls, v):
        return round(v, 2) if v is not None else None


class MarketComparisonResponse(BaseModel):
    """Response model for market comparison."""
    markets: List[MarketComparisonItem] = Field(..., description="Market comparison data")
    comparison_date: date = Field(..., description="Date of comparison data")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# ============================================================================
# User Management Models
# ============================================================================

class WatchlistItemCreate(BaseModel):
    """Request model for adding item to watchlist."""
    user_id: str = Field(..., description="User ID")
    metro_slug: str = Field(..., description="Metro slug to add to watchlist")


class WatchlistItem(BaseModel):
    """Response model for watchlist item."""
    watchlist_id: str = Field(..., description="Watchlist item ID")
    user_id: str = Field(..., description="User ID")
    metro_slug: Optional[str] = Field(None, description="Metro slug")
    metro_name: str = Field(..., description="Metro name")
    state_name: str = Field(..., description="State name")
    current_rent: Optional[float] = Field(None, description="Current rent value")
    yoy_pct_change: Optional[float] = Field(None, description="YoY change")
    mom_pct_change: Optional[float] = Field(None, description="MoM change")
    market_temperature: Optional[str] = Field(None, description="Market temperature")
    added_at: datetime = Field(..., description="Date added to watchlist")


class AlertCreate(BaseModel):
    """Request model for creating a price alert."""
    user_id: str = Field(..., description="User ID")
    metro_slug: str = Field(..., description="Metro slug for alert")
    alert_type: str = Field(..., description="Alert type: 'price_drop', 'threshold', 'trend'")
    threshold_value: Optional[float] = Field(None, description="Threshold value for alert (optional)")
    channel: str = Field("email", description="Notification channel: 'email' or 'sms'")
    cadence: str = Field("daily", description="Alert frequency: 'immediate', 'daily', 'weekly'")


class AlertUpdate(BaseModel):
    """Request model for updating a price alert."""
    alert_type: Optional[str] = Field(None, description="Alert type")
    threshold_value: Optional[float] = Field(None, description="Threshold value")
    channel: Optional[str] = Field(None, description="Notification channel")
    cadence: Optional[str] = Field(None, description="Alert frequency")
    active: Optional[bool] = Field(None, description="Whether alert is active")


class Alert(BaseModel):
    """Response model for price alert."""
    alert_id: str = Field(..., description="Alert ID")
    user_id: str = Field(..., description="User ID")
    metro_slug: Optional[str] = Field(None, description="Metro slug")
    metro_name: str = Field(..., description="Metro name")
    alert_type: str = Field(..., description="Alert type")
    threshold_value: Optional[float] = Field(None, description="Threshold value")
    channel: str = Field(..., description="Notification channel")
    cadence: str = Field(..., description="Alert frequency")
    active: bool = Field(..., description="Whether alert is active")
    created_at: datetime = Field(..., description="Alert creation date")
    last_triggered_at: Optional[datetime] = Field(None, description="Last trigger date")