"""
SQL queries for Tampa Rent Signals API.
Contains parameterized SQL queries for all API endpoints.
"""

from typing import Optional, List


class MarketQueries:
    """SQL queries for market-related endpoints."""
    
    @staticmethod
    def get_market_by_slug(metro_slug: str) -> str:
        """Get detailed information for a specific market by slug."""
        return f"""
        SELECT 
            l.location_business_key as metro_id,
            l.metro_slug,
            l.location_name as metro_name,
            l.state_name,
            l.latitude as lat,
            l.longitude as lng,
            l.market_size_category,
            l.population,
            rt.rent_value as current_rent,
            rt.yoy_pct_change,
            rt.mom_pct_change,
            rt.market_temperature,
            rt.data_quality_score,
            rt.data_source,
            rt.month_date as last_updated
        FROM RENTS.ANALYTICS.DIM_LOCATION l
        JOIN RENTS.MARTS.MART_RENT_TRENDS rt
            ON l.location_business_key = rt.location_business_key
        WHERE l.metro_slug = '{metro_slug}'
          AND rt.month_date = (SELECT MAX(month_date) FROM RENTS.MARTS.MART_RENT_TRENDS)
        LIMIT 1
        """
    
    @staticmethod
    def get_markets_summary(
        state_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> str:
        """Get summary of all available markets with geographic data."""
        base_query = """
        WITH latest_data AS (
            SELECT 
                l.location_business_key as metro_id,
                l.metro_slug,
                rt.metro_name,
                rt.state_name,
                rt.data_source,
                rt.rent_value,
                rt.yoy_pct_change,
                rt.mom_pct_change,
                rt.market_temperature,
                rt.market_size_category,
                rt.population,
                l.latitude as lat,
                l.longitude as lng,
                rt.month_date as last_updated,
                ROW_NUMBER() OVER (
                    PARTITION BY rt.metro_name, rt.state_name, rt.data_source 
                    ORDER BY rt.month_date DESC
                ) as rn
            FROM RENTS.MARTS.MART_RENT_TRENDS rt
            JOIN RENTS.ANALYTICS.DIM_LOCATION l
                ON rt.location_business_key = l.location_business_key
            WHERE rt.month_date >= DATEADD(month, -3, CURRENT_DATE())
        )
        SELECT 
            metro_id,
            metro_slug,
            metro_name,
            state_name,
            rent_value as current_rent,
            yoy_pct_change,
            mom_pct_change,
            market_temperature,
            market_size_category,
            population,
            data_source,
            lat,
            lng,
            last_updated
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
    def get_featured_markets(limit: int = 10) -> str:
        """Get top featured markets by growth and heat score."""
        return f"""
        SELECT 
            l.location_business_key as metro_id,
            l.metro_slug,
            rt.metro_name,
            rt.state_name,
            rt.rent_value as current_rent,
            rt.yoy_pct_change,
            rt.mom_pct_change,
            rt.market_temperature,
            l.latitude as lat,
            l.longitude as lng,
            mr.market_heat_score,
            rt.data_source,
            rt.month_date as last_updated
        FROM RENTS.MARTS.MART_RENT_TRENDS rt
        JOIN RENTS.ANALYTICS.DIM_LOCATION l
            ON rt.location_business_key = l.location_business_key
        LEFT JOIN RENTS.MARTS.MART_MARKET_RANKINGS mr
            ON rt.location_business_key = mr.location_business_key
            AND rt.month_date = mr.month_date
        WHERE rt.month_date = (SELECT MAX(month_date) FROM RENTS.MARTS.MART_RENT_TRENDS)
          AND rt.data_quality_score >= 7
        ORDER BY mr.market_heat_score DESC NULLS LAST,
                 rt.yoy_pct_change DESC NULLS LAST
        LIMIT {limit}
        """
    
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
    def get_heat_map_data() -> str:
        """Get market heat scores with geographic coordinates for heat map visualization."""
        return """
        SELECT 
            l.location_business_key as metro_id,
            l.metro_slug,
            l.location_name as metro_name,
            l.state_name,
            l.latitude as lat,
            l.longitude as lng,
            mr.market_heat_score,
            mr.growth_rank,
            mr.stability_rank,
            rt.rent_value as current_rent,
            rt.yoy_pct_change,
            rt.mom_pct_change,
            rt.market_temperature,
            rt.month_date as last_updated
        FROM RENTS.ANALYTICS.DIM_LOCATION l
        JOIN RENTS.MARTS.MART_RENT_TRENDS rt
            ON l.location_business_key = rt.location_business_key
        LEFT JOIN RENTS.MARTS.MART_MARKET_RANKINGS mr
            ON rt.location_business_key = mr.location_business_key
            AND rt.month_date = mr.month_date
        WHERE rt.month_date = (SELECT MAX(month_date) FROM RENTS.MARTS.MART_RENT_TRENDS)
          AND l.latitude IS NOT NULL
          AND l.longitude IS NOT NULL
          AND rt.data_quality_score >= 7
        ORDER BY mr.market_heat_score DESC NULLS LAST
        """
    
    @staticmethod
    def get_state_rankings(state: str, limit: int = 50) -> str:
        """Get market rankings for a specific state."""
        return f"""
        SELECT 
            l.location_business_key as metro_id,
            l.metro_slug,
            l.location_name as metro_name,
            l.state_name,
            rt.rent_value as current_rent,
            rt.yoy_pct_change,
            rt.mom_pct_change,
            rt.market_temperature,
            l.population,
            mr.market_heat_score,
            mr.growth_rank,
            mr.stability_rank,
            rt.data_source,
            rt.month_date as last_updated,
            RANK() OVER (ORDER BY rt.rent_value DESC) as state_rent_rank,
            RANK() OVER (ORDER BY rt.yoy_pct_change DESC) as state_growth_rank
        FROM RENTS.ANALYTICS.DIM_LOCATION l
        JOIN RENTS.MARTS.MART_RENT_TRENDS rt
            ON l.location_business_key = rt.location_business_key
        LEFT JOIN RENTS.MARTS.MART_MARKET_RANKINGS mr
            ON rt.location_business_key = mr.location_business_key
            AND rt.month_date = mr.month_date
        WHERE rt.month_date = (SELECT MAX(month_date) FROM RENTS.MARTS.MART_RENT_TRENDS)
          AND LOWER(l.state_name) = LOWER('{state}')
        ORDER BY mr.market_heat_score DESC NULLS LAST, rt.yoy_pct_change DESC
        LIMIT {limit}
        """
    
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
    def get_freshness_by_source() -> str:
        """Get data freshness status by source."""
        return """
        SELECT 
            source_name,
            latest_data_date,
            latest_load_date,
            record_count,
            data_quality_score as avg_quality_score,
            DATEDIFF(day, latest_data_date, CURRENT_DATE()) as days_since_update,
            CASE 
                WHEN DATEDIFF(day, latest_data_date, CURRENT_DATE()) <= 7 THEN 'Fresh'
                WHEN DATEDIFF(day, latest_data_date, CURRENT_DATE()) <= 14 THEN 'Recent'
                WHEN DATEDIFF(day, latest_data_date, CURRENT_DATE()) <= 30 THEN 'Aging'
                ELSE 'Stale'
            END as freshness_status
        FROM RENTS.MARTS.MART_DATA_LINEAGE
        ORDER BY latest_data_date DESC
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


class UserQueries:
    """SQL queries for user management endpoints (watchlist, alerts)."""
    
    @staticmethod
    def create_user_if_not_exists(user_id: str, email: str) -> str:
        """Create user if doesn't exist."""
        return f"""
        MERGE INTO RENTS.APPLICATION.USERS u
        USING (SELECT '{user_id}' as user_id, '{email}' as email) s
        ON u.user_id = s.user_id
        WHEN NOT MATCHED THEN
            INSERT (user_id, email) VALUES (s.user_id, s.email)
        """
    
    @staticmethod
    def add_to_watchlist(user_id: str, location_business_key: str, metro_slug: str) -> str:
        """Add market to user's watchlist."""
        return f"""
        INSERT INTO RENTS.APPLICATION.WATCHLIST (user_id, location_business_key, metro_slug)
        VALUES ('{user_id}', '{location_business_key}', '{metro_slug}')
        """
    
    @staticmethod
    def get_watchlist(user_id: str) -> str:
        """Get user's watchlist with current market data."""
        return f"""
        SELECT 
            w.watchlist_id,
            w.user_id,
            l.metro_slug,
            l.location_name as metro_name,
            l.state_name,
            rt.rent_value as current_rent,
            rt.yoy_pct_change,
            rt.mom_pct_change,
            rt.market_temperature,
            w.added_at
        FROM RENTS.APPLICATION.WATCHLIST w
        JOIN RENTS.ANALYTICS.DIM_LOCATION l
            ON w.location_business_key = l.location_business_key
        LEFT JOIN RENTS.MARTS.MART_RENT_TRENDS rt
            ON l.location_business_key = rt.location_business_key
            AND rt.month_date = (SELECT MAX(month_date) FROM RENTS.MARTS.MART_RENT_TRENDS)
        WHERE w.user_id = '{user_id}'
        ORDER BY w.added_at DESC
        """
    
    @staticmethod
    def remove_from_watchlist(watchlist_id: str) -> str:
        """Remove item from watchlist."""
        return f"""
        DELETE FROM RENTS.APPLICATION.WATCHLIST
        WHERE watchlist_id = '{watchlist_id}'
        """
    
    @staticmethod
    def lookup_location_key(metro_slug: str) -> str:
        """Lookup location_business_key from metro_slug."""
        return f"""
        SELECT location_business_key
        FROM RENTS.ANALYTICS.DIM_LOCATION
        WHERE metro_slug = '{metro_slug}'
        LIMIT 1
        """
    
    @staticmethod
    def create_alert(
        user_id: str,
        location_business_key: str,
        metro_slug: str,
        alert_type: str,
        threshold_value: Optional[float],
        channel: str,
        cadence: str
    ) -> str:
        """Create a price alert."""
        threshold_str = f"{threshold_value}" if threshold_value is not None else "NULL"
        return f"""
        INSERT INTO RENTS.APPLICATION.PRICE_ALERTS 
        (user_id, location_business_key, metro_slug, alert_type, threshold_value, channel, cadence)
        VALUES ('{user_id}', '{location_business_key}', '{metro_slug}', '{alert_type}', {threshold_str}, '{channel}', '{cadence}')
        """
    
    @staticmethod
    def get_alerts(user_id: str) -> str:
        """Get user's active alerts."""
        return f"""
        SELECT 
            a.alert_id,
            a.user_id,
            a.metro_slug,
            l.location_name as metro_name,
            a.alert_type,
            a.threshold_value,
            a.channel,
            a.cadence,
            a.active,
            a.created_at,
            a.last_triggered_at
        FROM RENTS.APPLICATION.PRICE_ALERTS a
        JOIN RENTS.ANALYTICS.DIM_LOCATION l
            ON a.location_business_key = l.location_business_key
        WHERE a.user_id = '{user_id}'
        ORDER BY a.created_at DESC
        """
    
    @staticmethod
    def update_alert(alert_id: str, updates: dict) -> str:
        """Update alert configuration."""
        set_clauses = []
        for key, value in updates.items():
            if isinstance(value, str):
                set_clauses.append(f"{key} = '{value}'")
            elif isinstance(value, bool):
                set_clauses.append(f"{key} = {value}")
            elif value is not None:
                set_clauses.append(f"{key} = {value}")
        
        if not set_clauses:
            return None
            
        return f"""
        UPDATE RENTS.APPLICATION.PRICE_ALERTS
        SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP()
        WHERE alert_id = '{alert_id}'
        """
    
    @staticmethod
    def delete_alert(alert_id: str) -> str:
        """Delete an alert."""
        return f"""
        DELETE FROM RENTS.APPLICATION.PRICE_ALERTS
        WHERE alert_id = '{alert_id}'
        """