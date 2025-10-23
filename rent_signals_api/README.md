# Tampa Rent Signals RESTful API

A production-ready FastAPI application that provides rental market data analysis, price tracking, and market intelligence for the Tampa Bay area and beyond.

## 🎯 Overview

This API leverages the Tampa Rent Signals data warehouse to provide:
- **Real-time rental market analysis** with price trends and comparisons
- **Price drop detection** for finding rental deals and market opportunities
- **Market rankings** by growth, heat scores, and investment potential
- **Economic correlation analysis** between rent prices and inflation
- **Regional market summaries** with state and metro-level insights

## 🚀 Quick Start

### Local Development

1. **Clone and Setup**
```bash
cd rent_signals_api
cp .env.example .env
# Edit .env with your Snowflake credentials
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the API**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access Documentation**
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/v1/health

### Docker Deployment

1. **Build and Run**
```bash
docker-compose up --build
```

2. **Production Build**
```bash
docker build -t rent-signals-api .
docker run -p 8000:8000 --env-file .env rent-signals-api
```

## 📍 API Endpoints

### **Base URL**: `http://localhost:8000/v1`

### 🏠 Market Data Endpoints

#### **GET /markets**
List all available rental markets with summary statistics.

**Query Parameters:**
- `state` (optional): Filter by state name
- `limit` (1-100, default 20): Results per page
- `offset` (default 0): Starting position

**Example:**
```bash
curl "http://localhost:8000/v1/markets?state=florida&limit=10"
```

#### **GET /markets/{metro_slug}/trends**
Historical rent trends for a specific metro area.

**Path Parameters:**
- `metro_slug`: Metro area slug (e.g., "tampa", "miami", "orlando")

**Query Parameters:**
- `months` (1-60, default 12): Number of months of historical data
- `data_source` (default "Zillow ZORI"): Data source

**Example:**
```bash
curl "http://localhost:8000/v1/markets/tampa/trends?months=24"
```

#### **GET /markets/compare**
Compare multiple rental markets side-by-side.

**Query Parameters:**
- `metros` (required): Comma-separated metro slugs (max 10)

**Example:**
```bash
curl "http://localhost:8000/v1/markets/compare?metros=tampa,miami,orlando"
```

### 💰 Price Analysis Endpoints

#### **GET /prices/drops**
Markets with recent significant price drops.

**Query Parameters:**
- `threshold` (0.1-50.0, default 5.0): Minimum price drop percentage
- `timeframe` ("week"|"month"|"quarter", default "month"): Time period
- `state` (optional): Filter by state name
- `limit`/`offset`: Pagination

**Example:**
```bash
curl "http://localhost:8000/v1/prices/drops?threshold=10&timeframe=month&state=florida"
```

### 🏆 Rankings Endpoints

#### **GET /rankings/top**
Top market rankings by various categories.

**Query Parameters:**
- `category` ("growth"|"rent"|"heat_score"|"investment", default "growth"): Ranking category
- `limit`/`offset`: Pagination

**Example:**
```bash
curl "http://localhost:8000/v1/rankings/top?category=heat_score&limit=25"
```

### 📊 Analytics Endpoints

#### **GET /economics/correlation**
Rent vs inflation correlation analysis with policy implications.

**Query Parameters:**
- `start_year` (optional): Starting year for analysis
- `limit`/`offset`: Pagination

**Example:**
```bash
curl "http://localhost:8000/v1/economics/correlation?start_year=2020"
```

#### **GET /regional/summary**
State and regional market aggregations.

**Query Parameters:**
- `state` (optional): Filter by state name
- `limit`/`offset`: Pagination

**Example:**
```bash
curl "http://localhost:8000/v1/regional/summary?state=florida"
```

### 🔍 Metadata Endpoints

#### **GET /data/lineage**
Data lineage and quality information for transparency.

#### **GET /meta/schema**
Database schema information for developers.

#### **GET /health**
Health check endpoint for monitoring.

## 📊 Response Examples

### Market Summary
```json
{
  "metro_name": "Tampa-St. Petersburg-Clearwater",
  "state_name": "Florida",
  "current_rent": 1850.00,
  "yoy_pct_change": 12.5,
  "mom_pct_change": 2.1,
  "market_temperature": "Hot",
  "market_size_category": "Large Metro (1M-5M)",
  "population": 3175275,
  "data_source": "Zillow ZORI"
}
```

### Price Drop
```json
{
  "metro_name": "Orlando-Kissimmee-Sanford",
  "state_name": "Florida",
  "current_rent": 1650.00,
  "price_change_pct": -8.5,
  "change_period": "month",
  "market_temperature": "Cool",
  "month_date": "2024-01-01",
  "data_source": "Zillow ZORI"
}
```

### Market Ranking
```json
{
  "metro_name": "Austin-Round Rock",
  "state_name": "Texas",
  "market_size_category": "Large Metro (1M-5M)",
  "rank": 1,
  "score": 89.5,
  "metric_value": 18.2,
  "population": 2352426
}
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Snowflake Database Connection
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=RENTS
SNOWFLAKE_WAREHOUSE=WH_XS
SNOWFLAKE_ROLE=ACCOUNTADMIN

# API Configuration
API_TITLE=Tampa Rent Signals API
API_VERSION=1.0.0
CACHE_TTL_SECONDS=3600
MAX_QUERY_LIMIT=100

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Data Sources

The API queries data from these mart tables:
- `RENTS.MARTS.MART_RENT_TRENDS` - Cross-source rent analysis
- `RENTS.MARTS.MART_MARKET_RANKINGS` - Market competitiveness scores
- `RENTS.MARTS.MART_ECONOMIC_CORRELATION` - Economic analysis
- `RENTS.MARTS.MART_REGIONAL_SUMMARY` - Regional aggregations
- `RENTS.MARTS.MART_DATA_LINEAGE` - Data quality monitoring

## 🛡️ Error Handling

The API provides structured error responses:

```json
{
  "error": "HTTP_ERROR",
  "message": "No data found for metro: invalid-metro",
  "details": {
    "status_code": 404
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (no data for query)
- `422`: Validation Error (invalid input format)
- `500`: Internal Server Error
- `503`: Service Unavailable (database issues)

## 📈 Performance & Caching

### Query Optimization
- Leverages pre-aggregated mart tables for fast responses
- Uses pagination to limit result sizes
- Implements connection pooling for database efficiency

### Response Times
- **Market summaries**: < 200ms
- **Trend data**: < 500ms
- **Complex analytics**: < 1000ms

### Future Caching Strategy
- Market data: 6 hours TTL
- Trend data: 1 hour TTL
- Rankings: 12 hours TTL
- Real-time drops: No caching

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
```bash
# Set production environment variables
export ENVIRONMENT=production
export DEBUG=false
export LOG_LEVEL=INFO
```

2. **Container Deployment**
```bash
# Build production image
docker build -t rent-signals-api:latest .

# Run with production settings
docker run -d \
  --name rent-signals-api \
  -p 8000:8000 \
  --env-file .env.production \
  --restart unless-stopped \
  rent-signals-api:latest
```

3. **Load Balancer Configuration**
- Configure health checks to `/v1/health`
- Set up SSL termination
- Enable GZIP compression
- Configure rate limiting

### Monitoring

#### Health Checks
```bash
# Basic health check
curl http://localhost:8000/v1/health

# Detailed status
curl http://localhost:8000/v1/data/lineage
```

#### Logging
The API uses structured JSON logging:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "event": "Request completed",
  "method": "GET",
  "url": "/v1/markets",
  "status_code": 200,
  "process_time": 0.156,
  "client_ip": "192.168.1.100"
}
```

#### Metrics to Monitor
- Request volume and response times
- Error rates by endpoint
- Database connection health
- Cache hit rates (when implemented)

## 🧪 Testing

### Manual Testing
```bash
# Test basic functionality
curl http://localhost:8000/v1/health
curl http://localhost:8000/v1/markets?limit=5
curl http://localhost:8000/v1/prices/drops?threshold=5

# Test error handling
curl http://localhost:8000/v1/markets/invalid-metro/trends
```

### Load Testing
```bash
# Using wrk for load testing
wrk -t4 -c100 -d30s --latency http://localhost:8000/v1/markets
```

## 🔮 Future Enhancements

### Phase 2 Features
- **User Authentication**: JWT-based auth with API keys
- **Alert System**: POST endpoints for price drop alerts
- **WebSocket Support**: Real-time price updates
- **Caching Layer**: Redis integration for performance

### Advanced Features
- **Machine Learning**: Price prediction endpoints
- **Geospatial Queries**: Radius-based market searches
- **Bulk Data Access**: CSV/JSON export endpoints
- **Webhook Integration**: External system notifications

## 🤝 API Usage Examples

### Rental Market Analysis App
```javascript
// Find markets with recent price drops
const priceDrops = await fetch('/v1/prices/drops?threshold=10&state=florida')
  .then(r => r.json());

// Compare multiple markets
const comparison = await fetch('/v1/markets/compare?metros=tampa,miami,orlando')
  .then(r => r.json());

// Get trending markets
const topGrowth = await fetch('/v1/rankings/top?category=growth&limit=10')
  .then(r => r.json());
```

### Investment Analysis Dashboard
```python
import requests

# Analyze market opportunities
def find_investment_opportunities(state='florida', drop_threshold=15):
    drops = requests.get(f'/v1/prices/drops?threshold={drop_threshold}&state={state}')
    rankings = requests.get('/v1/rankings/top?category=investment')
    
    # Combine data for investment scoring
    return analyze_opportunities(drops.json(), rankings.json())
```

### Real Estate Market Report
```bash
# Generate weekly market report
curl "/v1/regional/summary?state=florida" | jq '.summaries[]' > florida_summary.json
curl "/v1/economics/correlation?start_year=2023" | jq '.data[]' > economic_trends.json
curl "/v1/prices/drops?threshold=5&timeframe=week" | jq '.drops[]' > weekly_drops.json
```

## 📞 Support

For API issues or questions:
1. Check the `/v1/health` endpoint for system status
2. Review the interactive documentation at `/docs`
3. Examine application logs for detailed error information
4. Validate your Snowflake connection credentials