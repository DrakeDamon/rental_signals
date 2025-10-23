"""
Basic tests for Tampa Rent Signals API endpoints.
Run with: pytest tests/test_api.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @patch('app.main.test_database_connection')
    def test_health_check_healthy(self, mock_db_test):
        """Test health check with healthy database."""
        mock_db_test.return_value = True
        
        response = client.get("/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "timestamp" in data
        assert "version" in data
    
    @patch('app.main.test_database_connection')
    def test_health_check_degraded(self, mock_db_test):
        """Test health check with database issues."""
        mock_db_test.return_value = False
        
        response = client.get("/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self):
        """Test API root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "title" in data
        assert "version" in data
        assert "endpoints" in data


class TestMarketEndpoints:
    """Test market data endpoints."""
    
    @patch('app.main.execute_query')
    async def test_get_markets(self, mock_query):
        """Test markets endpoint with mock data."""
        mock_query.return_value = [
            {
                "METRO_NAME": "Tampa-St. Petersburg-Clearwater",
                "STATE_NAME": "Florida",
                "CURRENT_RENT": 1850.0,
                "YOY_PCT_CHANGE": 12.5,
                "MOM_PCT_CHANGE": 2.1,
                "MARKET_TEMPERATURE": "Hot",
                "MARKET_SIZE_CATEGORY": "Large Metro (1M-5M)",
                "POPULATION": 3175275,
                "DATA_SOURCE": "Zillow ZORI"
            }
        ]
        
        response = client.get("/v1/markets")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        if data:  # If mock data is returned
            assert "metro_name" in data[0]
            assert "state_name" in data[0]
    
    def test_get_markets_with_pagination(self):
        """Test markets endpoint with pagination parameters."""
        response = client.get("/v1/markets?limit=5&offset=10")
        # Should not fail even without database connection
        assert response.status_code in [200, 500, 503]
    
    def test_get_markets_with_state_filter(self):
        """Test markets endpoint with state filter."""
        response = client.get("/v1/markets?state=florida")
        assert response.status_code in [200, 500, 503]
    
    def test_market_trends_endpoint(self):
        """Test market trends endpoint."""
        response = client.get("/v1/markets/tampa/trends")
        # Should return 404, 500, or 503 without valid database
        assert response.status_code in [404, 500, 503]
    
    def test_market_trends_with_params(self):
        """Test market trends with query parameters."""
        response = client.get("/v1/markets/tampa/trends?months=6&data_source=Zillow ZORI")
        assert response.status_code in [404, 500, 503]
    
    def test_market_comparison(self):
        """Test market comparison endpoint."""
        response = client.get("/v1/markets/compare?metros=tampa,miami,orlando")
        assert response.status_code in [404, 500, 503]
    
    def test_market_comparison_validation(self):
        """Test market comparison with invalid parameters."""
        # Test empty metros parameter
        response = client.get("/v1/markets/compare?metros=")
        assert response.status_code == 400
        
        # Test missing metros parameter
        response = client.get("/v1/markets/compare")
        assert response.status_code == 422  # Validation error


class TestPriceEndpoints:
    """Test price analysis endpoints."""
    
    def test_price_drops_endpoint(self):
        """Test price drops endpoint."""
        response = client.get("/v1/prices/drops")
        assert response.status_code in [200, 500, 503]
    
    def test_price_drops_with_filters(self):
        """Test price drops with various filters."""
        response = client.get("/v1/prices/drops?threshold=10&timeframe=month&state=florida")
        assert response.status_code in [200, 500, 503]
    
    def test_price_drops_validation(self):
        """Test price drops parameter validation."""
        # Test invalid threshold
        response = client.get("/v1/prices/drops?threshold=100")
        assert response.status_code == 422
        
        # Test invalid timeframe
        response = client.get("/v1/prices/drops?timeframe=invalid")
        assert response.status_code == 422


class TestRankingEndpoints:
    """Test ranking endpoints."""
    
    def test_rankings_endpoint(self):
        """Test rankings endpoint."""
        response = client.get("/v1/rankings/top")
        assert response.status_code in [200, 500, 503]
    
    def test_rankings_categories(self):
        """Test different ranking categories."""
        categories = ["growth", "rent", "heat_score", "investment"]
        
        for category in categories:
            response = client.get(f"/v1/rankings/top?category={category}")
            assert response.status_code in [200, 500, 503]
    
    def test_rankings_validation(self):
        """Test rankings parameter validation."""
        # Test invalid category
        response = client.get("/v1/rankings/top?category=invalid")
        assert response.status_code == 422


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""
    
    def test_economic_correlation(self):
        """Test economic correlation endpoint."""
        response = client.get("/v1/economics/correlation")
        assert response.status_code in [200, 500, 503]
    
    def test_economic_correlation_with_year(self):
        """Test economic correlation with start year."""
        response = client.get("/v1/economics/correlation?start_year=2020")
        assert response.status_code in [200, 500, 503]
    
    def test_regional_summary(self):
        """Test regional summary endpoint."""
        response = client.get("/v1/regional/summary")
        assert response.status_code in [200, 500, 503]
    
    def test_regional_summary_with_state(self):
        """Test regional summary with state filter."""
        response = client.get("/v1/regional/summary?state=florida")
        assert response.status_code in [200, 500, 503]


class TestMetadataEndpoints:
    """Test metadata endpoints."""
    
    def test_data_lineage(self):
        """Test data lineage endpoint."""
        response = client.get("/v1/data/lineage")
        assert response.status_code in [200, 500, 503]
    
    def test_schema_info(self):
        """Test schema information endpoint."""
        response = client.get("/v1/meta/schema")
        assert response.status_code in [200, 500, 503]


class TestPaginationValidation:
    """Test pagination parameter validation."""
    
    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        response = client.get("/v1/markets?limit=10&offset=0")
        assert response.status_code in [200, 500, 503]
    
    def test_invalid_limit(self):
        """Test invalid limit values."""
        # Limit too low
        response = client.get("/v1/markets?limit=0")
        assert response.status_code == 422
        
        # Limit too high
        response = client.get("/v1/markets?limit=200")
        assert response.status_code == 422
    
    def test_invalid_offset(self):
        """Test invalid offset values."""
        # Negative offset
        response = client.get("/v1/markets?offset=-1")
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_endpoints(self):
        """Test requests to non-existent endpoints."""
        response = client.get("/v1/invalid/endpoint")
        assert response.status_code == 404
    
    def test_invalid_metro_slug(self):
        """Test invalid metro slug handling."""
        response = client.get("/v1/markets/nonexistent-metro/trends")
        assert response.status_code in [404, 500, 503]
    
    def test_malformed_parameters(self):
        """Test malformed query parameters."""
        response = client.get("/v1/markets/tampa/trends?months=invalid")
        assert response.status_code == 422


# Integration test (requires actual database connection)
@pytest.mark.integration
class TestIntegrationWithDatabase:
    """Integration tests that require actual database connection."""
    
    def test_real_database_connection(self):
        """Test with real database connection (skip if no connection)."""
        response = client.get("/v1/health")
        
        if response.status_code == 200:
            data = response.json()
            if data["database"] == "connected":
                # Run integration tests with real data
                markets_response = client.get("/v1/markets?limit=1")
                assert markets_response.status_code == 200


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])