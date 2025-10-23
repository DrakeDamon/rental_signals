"""
Utility functions for Tampa Rent Signals API.
Includes URL normalization, data formatting, and helper functions.
"""

import re
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import structlog

logger = structlog.get_logger(__name__)


def normalize_metro_slug(metro_name: str) -> str:
    """
    Convert metro name to consistent lowercase slug for URL matching.
    
    Examples:
        "Tampa-St. Petersburg-Clearwater" → "tampa-st-petersburg-clearwater"
        "Miami-Fort Lauderdale" → "miami-fort-lauderdale"
        "Orlando" → "orlando"
    
    Args:
        metro_name: Original metro area name
        
    Returns:
        Normalized slug for consistent URL routing
    """
    if not metro_name:
        return ""
    
    # Convert to lowercase and replace spaces/punctuation with hyphens
    slug = metro_name.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove punctuation except hyphens
    slug = re.sub(r'\s+', '-', slug)      # Replace spaces with hyphens
    slug = re.sub(r'-+', '-', slug)       # Collapse multiple hyphens
    slug = slug.strip('-')                # Remove leading/trailing hyphens
    
    logger.debug("Metro slug normalized", original=metro_name, normalized=slug)
    return slug


def normalize_state_name(state_name: str) -> str:
    """
    Normalize state name for consistent querying.
    
    Args:
        state_name: State name in any case
        
    Returns:
        Properly capitalized state name
    """
    if not state_name:
        return ""
    
    # Handle common abbreviations
    state_abbreviations = {
        "fl": "Florida",
        "ca": "California", 
        "tx": "Texas",
        "ny": "New York",
        "il": "Illinois"
    }
    
    normalized = state_name.lower().strip()
    
    # Check if it's an abbreviation
    if normalized in state_abbreviations:
        return state_abbreviations[normalized]
    
    # Otherwise, title case
    return state_name.title()


def format_percentage(value: Optional[float], decimal_places: int = 1) -> Optional[str]:
    """
    Format a decimal percentage value for display.
    
    Args:
        value: Decimal percentage (e.g., 0.125 for 12.5%)
        decimal_places: Number of decimal places to show
        
    Returns:
        Formatted percentage string or None
    """
    if value is None:
        return None
    
    return f"{value:.{decimal_places}f}%"


def format_currency(value: Optional[float], include_symbol: bool = True) -> Optional[str]:
    """
    Format a currency value for display.
    
    Args:
        value: Currency amount
        include_symbol: Whether to include $ symbol
        
    Returns:
        Formatted currency string or None
    """
    if value is None:
        return None
    
    formatted = f"{value:,.0f}"
    return f"${formatted}" if include_symbol else formatted


def validate_date_range(start_date: Optional[date], end_date: Optional[date]) -> tuple:
    """
    Validate and normalize date range parameters.
    
    Args:
        start_date: Start date (optional)
        end_date: End date (optional)
        
    Returns:
        Tuple of (validated_start, validated_end)
        
    Raises:
        ValueError: If date range is invalid
    """
    today = date.today()
    
    # Set defaults if not provided
    if end_date is None:
        end_date = today
    
    if start_date is None:
        # Default to 1 year ago
        start_date = date(end_date.year - 1, end_date.month, end_date.day)
    
    # Validate range
    if start_date > end_date:
        raise ValueError("Start date must be before end date")
    
    if end_date > today:
        raise ValueError("End date cannot be in the future")
    
    # Limit range to reasonable bounds (e.g., 5 years)
    max_range_days = 5 * 365
    if (end_date - start_date).days > max_range_days:
        raise ValueError(f"Date range cannot exceed {max_range_days} days")
    
    return start_date, end_date


def paginate_results(
    results: List[Dict[str, Any]], 
    limit: int, 
    offset: int,
    total_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Format paginated results with metadata.
    
    Args:
        results: Query results
        limit: Results per page
        offset: Starting position
        total_count: Total number of available results (if known)
        
    Returns:
        Dictionary with results and pagination metadata
    """
    if total_count is None:
        total_count = len(results)
    
    return {
        "data": results,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "count": len(results),
            "total": total_count,
            "has_more": (offset + limit) < total_count,
            "next_offset": offset + limit if (offset + limit) < total_count else None
        }
    }


def sanitize_query_param(param: str, max_length: int = 100) -> str:
    """
    Sanitize query parameters to prevent injection attacks.
    
    Args:
        param: Query parameter value
        max_length: Maximum allowed length
        
    Returns:
        Sanitized parameter value
        
    Raises:
        ValueError: If parameter is invalid
    """
    if not param:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[^\w\s\-\.]', '', param)
    
    # Limit length
    if len(sanitized) > max_length:
        raise ValueError(f"Parameter too long (max {max_length} characters)")
    
    return sanitized.strip()


def build_where_clause(conditions: List[str], operator: str = "AND") -> str:
    """
    Build SQL WHERE clause from list of conditions.
    
    Args:
        conditions: List of SQL condition strings
        operator: SQL operator to join conditions (AND/OR)
        
    Returns:
        Complete WHERE clause or empty string
    """
    if not conditions:
        return ""
    
    return f"WHERE {f' {operator} '.join(conditions)}"


def extract_numeric_value(value: Any) -> Optional[float]:
    """
    Safely extract numeric value from various input types.
    
    Args:
        value: Input value of any type
        
    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None
    
    try:
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove common formatting characters
            cleaned = re.sub(r'[,$%]', '', value.strip())
            return float(cleaned)
        
        return None
    except (ValueError, TypeError):
        return None


class MarketTemperatureClassifier:
    """Helper class for market temperature classification logic."""
    
    @staticmethod
    def classify_temperature(yoy_change: Optional[float]) -> str:
        """
        Classify market temperature based on year-over-year change.
        
        Args:
            yoy_change: Year-over-year percentage change
            
        Returns:
            Market temperature classification
        """
        if yoy_change is None:
            return "Unknown"
        
        if yoy_change >= 15:
            return "Very Hot"
        elif yoy_change >= 10:
            return "Hot"
        elif yoy_change >= 5:
            return "Warm"
        elif yoy_change >= 0:
            return "Cool"
        else:
            return "Cold"
    
    @staticmethod
    def get_temperature_color(temperature: str) -> str:
        """Get color code for temperature visualization."""
        color_map = {
            "Very Hot": "#ff4444",
            "Hot": "#ff8800",
            "Warm": "#ffdd00",
            "Cool": "#88cc88",
            "Cold": "#4488cc",
            "Unknown": "#888888"
        }
        return color_map.get(temperature, "#888888")