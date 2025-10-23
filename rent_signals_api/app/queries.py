"""
SQL queries for Tampa Rent Signals API.
Contains parameterized SQL queries for all API endpoints.
"""

from typing import Optional, List


class MarketQueries:
    """SQL queries for market-related endpoints."""
    
    @staticmethod
    def get_markets_summary(
        state_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> str:
        """Get summary of all available markets."""
        base_query = """
        WITH latest_data AS (
            SELECT 
                metro_name,
                state_name,
                data_source,
                rent_value,
                yoy_pct_change,
                mom_pct_change,
                market_temperature,
                market_size_category,
                population,
                month_date,
                ROW_NUMBER() OVER (
                    PARTITION BY metro_name, state_name, data_source 
                    ORDER BY month_date DESC
                ) as rn
            FROM RENTS.MARTS.MART_RENT_TRENDS
            WHERE month_date >= DATEADD(month, -3, CURRENT_DATE())
        )
        SELECT 
            metro_name,
            state_name,
            rent_value as current_rent,
            yoy_pct_change,
            mom_pct_change,
            market_temperature,
            market_size_category,
            population,
            data_source
        FROM latest_data
        WHERE rn = 1
        """
        
        # Add state filter if provided
        if state_filter:
            base_query += " AND LOWER(state_name) = %(state_filter)s"
        
        base_query += """
        ORDER BY rent_value DESC NULLS LAST
        LIMIT %(limit)s OFFSET %(offset)s
        """
        
        return base_query
    
    @staticmethod
    def get_market_trends(
        metro_slug: str,
        data_source: str = "Zillow ZORI",
        months: int = 12
    ) -> str:
        """Get historical trends for a specific market."""
        return """
        SELECT 
            metro_name,
            state_name,
            month_date,
            rent_value,
            yoy_pct_change,
            mom_pct_change,
            market_temperature,
            data_source
        FROM RENTS.MARTS.MART_RENT_TRENDS 
        WHERE LOWER(REPLACE(REPLACE(metro_name, ' ', '-'), ',', '')) = %(metro_slug)s
          AND data_source = %(data_source)s
          AND month_date >= DATEADD(month, -%(months)s, CURRENT_DATE())
        ORDER BY month_date DESC
        """
    
    @staticmethod
    def get_market_comparison(metro_slugs: List[str]) -> str:
        """Get comparison data for multiple markets."""
        # Create IN clause for metro slugs
        slug_placeholders = ','.join([f"%(metro_slug_{i})s" for i in range(len(metro_slugs))])
        
        return f"""
        WITH latest_data AS (
            SELECT 
                metro_name,
                state_name,
                rent_value,
                yoy_pct_change,
                mom_pct_change,
                market_temperature,
                population,
                month_date,
                ROW_NUMBER() OVER (
                    PARTITION BY metro_name, state_name 
                    ORDER BY month_date DESC
                ) as rn
            FROM RENTS.MARTS.MART_RENT_TRENDS
            WHERE LOWER(REPLACE(REPLACE(metro_name, ' ', '-'), ',', '')) IN ({slug_placeholders})
              AND data_source = 'Zillow ZORI'
              AND month_date >= DATEADD(month, -3, CURRENT_DATE())
        ),
        ranked_data AS (
            SELECT 
                *,
                RANK() OVER (ORDER BY rent_value DESC) as rank_rent,
                RANK() OVER (ORDER BY yoy_pct_change DESC) as rank_growth
            FROM latest_data
            WHERE rn = 1
        )
        SELECT 
            metro_name,
            state_name,
            rent_value as current_rent,
            yoy_pct_change,
            mom_pct_change,
            market_temperature,
            population,
            rank_rent,
            rank_growth,
            month_date as comparison_date
        FROM ranked_data
        ORDER BY rank_rent
        """


class PriceQueries:
    """SQL queries for price-related endpoints."""
    
    @staticmethod
    def get_price_drops(
        threshold: float = 5.0,
        timeframe: str = "month",
        state_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> str:
        """Get markets with recent price drops."""
        
        # Map timeframe to column
        timeframe_column = {
            "week": "wow_pct_change",
            "month": "mom_pct_change",
            "quarter": "yoy_pct_change"
        }.get(timeframe, "mom_pct_change")
        
        base_query = f"""
        SELECT 
            metro_name,
            state_name,
            rent_value as current_rent,
            {timeframe_column} as price_change_pct,
            market_temperature,
            month_date,
            data_source
        FROM RENTS.MARTS.MART_RENT_TRENDS
        WHERE {timeframe_column} <= -%(threshold)s
          AND month_date >= DATEADD(month, -3, CURRENT_DATE())
          AND data_source = 'Zillow ZORI'
        """
        
        if state_filter:
            base_query += " AND LOWER(state_name) = %(state_filter)s"
        
        base_query += f"""
        ORDER BY {timeframe_column} ASC
        LIMIT %(limit)s OFFSET %(offset)s
        """
        
        return base_query
    
    @staticmethod
    def count_price_drops(
        threshold: float = 5.0,
        timeframe: str = "month",
        state_filter: Optional[str] = None
    ) -> str:
        """Count total price drops for pagination."""
        
        timeframe_column = {
            "week": "wow_pct_change",
            "month": "mom_pct_change", 
            "quarter": "yoy_pct_change"
        }.get(timeframe, "mom_pct_change")
        
        base_query = f"""
        SELECT COUNT(*) as total_count
        FROM RENTS.MARTS.MART_RENT_TRENDS
        WHERE {timeframe_column} <= -%(threshold)s
          AND month_date >= DATEADD(month, -3, CURRENT_DATE())
          AND data_source = 'Zillow ZORI'
        """
        
        if state_filter:
            base_query += " AND LOWER(state_name) = %(state_filter)s"
        
        return base_query


class RankingQueries:
    """SQL queries for ranking endpoints."""
    
    @staticmethod
    def get_top_rankings(
        category: str = "growth",
        limit: int = 10,
        offset: int = 0
    ) -> str:
        """Get top market rankings by category."""
        
        # Map category to appropriate column and source
        category_config = {
            "growth": {
                "metric": "yoy_pct_change",
                "order": "DESC",
                "source": "MART_RENT_TRENDS"
            },
            "rent": {
                "metric": "rent_value", 
                "order": "DESC",
                "source": "MART_RENT_TRENDS"
            },
            "heat_score": {
                "metric": "market_heat_score",
                "order": "DESC", 
                "source": "MART_MARKET_RANKINGS"
            },
            "investment": {
                "metric": "investment_attractiveness_score",
                "order": "DESC",
                "source": "MART_RENT_TRENDS"
            }
        }
        
        config = category_config.get(category, category_config["growth"])
        
        if config["source"] == "MART_MARKET_RANKINGS":
            return f"""
            SELECT 
                location_name as metro_name,
                state_name,
                market_size_category,
                {config["metric"]} as score,
                {config["metric"]} as metric_value,
                population,
                RANK() OVER (ORDER BY {config["metric"]} {config["order"]}) as rank
            FROM RENTS.MARTS.MART_MARKET_RANKINGS
            WHERE {config["metric"]} IS NOT NULL
            ORDER BY {config["metric"]} {config["order"]}
            LIMIT %(limit)s OFFSET %(offset)s
            """
        else:
            return f"""
            WITH latest_data AS (
                SELECT 
                    metro_name,
                    state_name,
                    market_size_category,
                    population,
                    {config["metric"]},
                    month_date,
                    ROW_NUMBER() OVER (
                        PARTITION BY metro_name, state_name 
                        ORDER BY month_date DESC
                    ) as rn
                FROM RENTS.MARTS.MART_RENT_TRENDS
                WHERE data_source = 'Zillow ZORI'
                  AND {config["metric"]} IS NOT NULL
                  AND month_date >= DATEADD(month, -3, CURRENT_DATE())
            ),
            ranked_data AS (
                SELECT 
                    metro_name,
                    state_name,
                    market_size_category,
                    population,
                    {config["metric"]} as score,
                    {config["metric"]} as metric_value,
                    RANK() OVER (ORDER BY {config["metric"]} {config["order"]}) as rank
                FROM latest_data
                WHERE rn = 1
            )
            SELECT 
                metro_name,
                state_name,
                market_size_category,
                score,
                metric_value,
                population,
                rank
            FROM ranked_data
            ORDER BY rank
            LIMIT %(limit)s OFFSET %(offset)s
            """


class EconomicQueries:
    """SQL queries for economic analysis endpoints."""
    
    @staticmethod
    def get_economic_correlation(
        start_year: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """Get economic correlation data."""
        base_query = """
        SELECT 
            year,
            quarter,
            economic_regime,
            rent_cpi_correlation,
            affordability_pressure,
            policy_implications,
            rent_housing_cpi_spread
        FROM RENTS.MARTS.MART_ECONOMIC_CORRELATION
        WHERE 1=1
        """
        
        if start_year:
            base_query += " AND year >= %(start_year)s"
        
        base_query += """
        ORDER BY year DESC, quarter DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """
        
        return base_query


class RegionalQueries:
    """SQL queries for regional analysis endpoints."""
    
    @staticmethod
    def get_regional_summary(
        state_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """Get regional market summaries."""
        base_query = """
        SELECT 
            state_name,
            region_name,
            metro_count,
            avg_rent_index,
            weighted_yoy_growth,
            dominant_trend,
            total_population,
            market_concentration
        FROM RENTS.MARTS.MART_REGIONAL_SUMMARY
        WHERE 1=1
        """
        
        if state_filter:
            base_query += " AND LOWER(state_name) = %(state_filter)s"
        
        base_query += """
        ORDER BY avg_rent_index DESC NULLS LAST
        LIMIT %(limit)s OFFSET %(offset)s
        """
        
        return base_query


class MetaQueries:
    """SQL queries for metadata and system information."""
    
    @staticmethod
    def get_data_lineage() -> str:
        """Get data lineage and quality information."""
        return """
        SELECT 
            table_name,
            layer,
            source_name,
            data_freshness_status,
            data_quality_status,
            overall_reliability_score,
            days_since_latest_data,
            last_updated
        FROM RENTS.MARTS.MART_DATA_LINEAGE
        ORDER BY overall_reliability_score DESC, last_updated DESC
        """
    
    @staticmethod
    def test_connection() -> str:
        """Simple query to test database connectivity."""
        return "SELECT 1 as test_result, CURRENT_TIMESTAMP() as timestamp"
    
    @staticmethod
    def get_schema_info() -> str:
        """Get schema information for API documentation."""
        return """
        SELECT 
            table_schema,
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_schema IN ('STAGING', 'CORE', 'MARTS')
          AND table_name LIKE 'MART_%'
        ORDER BY table_schema, table_name, ordinal_position
        """