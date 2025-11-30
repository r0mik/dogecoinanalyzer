# DogeAnalyze - Dogecoin Data Collection & Analysis Platform

## Project Overview

DogeAnalyze is a comprehensive platform for collecting, analyzing, and visualizing Dogecoin market data. The system consists of:

1. **Data Collector Service** - Fetches real-time Dogecoin data (price, volume, market cap, etc.) from free APIs (CoinGecko, CryptoCompare, Binance)
2. **Analysis Bot Service** - Performs technical analysis and generates predictions for 1h, 4h, 24h, 7d, and 30d timeframes
3. **Web Dashboard** - Flask-based web interface displaying real-time data, script statuses, and analysis results

## Architecture

```
┌─────────────────┐
│  Data Collector │──┐
│   (Container)   │  │
└─────────────────┘  │
                      ├──► PostgreSQL Database
┌─────────────────┐  │     (Container)
│  Analysis Bot   │──┘
│   (Container)   │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Web Dashboard  │
│   (Container)   │
│   (Flask/FastAPI)│
└─────────────────┘
```

**All services run in separate Docker containers for easy deployment and scaling.**

## Implementation Status

### Phase 1: Project Setup & Infrastructure ✅
- [x] Create project structure
- [x] Set up Python virtual environment
- [x] Initialize database schema (PostgreSQL)
- [x] Configure environment variables
- [x] Set up logging system

### Phase 2: Data Collector Script ✅
- [x] Research and select free Dogecoin data APIs (CoinGecko, CryptoCompare, Binance API)
- [x] Implement data fetching module with multiple API clients
- [x] Create database models for raw market data
- [x] Implement scheduled data collection (APScheduler)
- [x] Add error handling and retry logic
- [x] Add data validation
- [x] Rate limiting for API calls

### Phase 3: Analysis Bot ✅
- [x] Implement technical indicators (RSI, MACD, Moving Averages, Bollinger Bands)
- [x] Create prediction models for 1h, 4h, 24h, 7d, 30d timeframes
- [x] Design database schema for analysis results
- [x] Implement analysis execution logic
- [x] Add confidence scoring for predictions
- [x] Schedule periodic analysis runs
- [x] Local LLM model integration (optional, for enhanced reasoning)

### Phase 4: Web Dashboard ✅
- [x] Set up web framework (Flask)
- [x] Create API endpoints for:
  - Current market data (`/api/current`)
  - Historical data (`/api/history`)
  - Analysis results (`/api/analysis`)
  - Script statuses (`/api/status`)
  - Health check (`/api/health`)
  - Dashboard statistics (`/api/stats`)
- [x] Build frontend dashboard with:
  - Real-time price charts
  - Script status indicators
  - Analysis results display
  - Historical data visualization

### Phase 5: Integration & Testing 🚧
- [x] Integrate all components
- [x] Docker containerization
- [x] Health checks and monitoring
- [ ] Comprehensive test suite
- [ ] Performance optimization

### Phase 6: Deployment & Documentation ✅
- [x] Create deployment scripts (Docker Compose)
- [x] Makefile for common operations
- [x] Docker documentation
- [x] Quick start guide
- [x] Architecture documentation

## Project Structure

```
dogeanalyze/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   ├── __init__.py
│   └── settings.py
├── collector/
│   ├── __init__.py
│   ├── data_fetcher.py
│   ├── api_clients.py
│   └── scheduler.py
├── analyzer/
│   ├── __init__.py
│   ├── technical_indicators.py
│   ├── predictor.py
│   ├── db_helper.py
│   └── local_model.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   ├── db_manager.py
│   └── migrations/
├── dashboard/
│   ├── __init__.py
│   ├── app.py
│   ├── routes.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       └── index.html
├── utils/
│   ├── __init__.py
│   └── logger.py
└── tests/
    ├── test_collector.py
    ├── test_analyzer.py
    └── test_dashboard.py
```

## Technology Stack

### Backend
- **Python 3.11** - Main programming language
- **SQLAlchemy 2.0** - ORM for database operations
- **PostgreSQL 15** - Production database (via Docker)
- **Flask 3.0** - Web framework for dashboard
- **APScheduler** - Task scheduling for data collection and analysis
- **Requests** - HTTP client for API calls
- **Pandas** - Data manipulation for analysis
- **NumPy** - Numerical computations
- **TA-Lib (ta)** - Technical analysis library

### Frontend
- **HTML/CSS/JavaScript** - Basic frontend
- **Chart.js/D3.js** - Data visualization
- **Bootstrap/Tailwind CSS** - UI framework

### APIs (Free Sources)
- **CoinGecko API** - Free tier available
- **CryptoCompare API** - Free tier available
- **Binance Public API** - Free, no authentication needed for public data

## Database Schema

### Market Data Table
- `id` - Primary key
- `timestamp` - Data collection time
- `price_usd` - Current price in USD
- `volume_24h` - 24h trading volume
- `market_cap` - Market capitalization
- `price_change_24h` - 24h price change percentage
- `high_24h` - 24h high price
- `low_24h` - 24h low price
- `source` - API source name

### Analysis Results Table
- `id` - Primary key
- `timestamp` - Analysis execution time
- `timeframe` - Prediction timeframe (1h, 4h, 24h, 7d, 30d)
- `predicted_price` - Predicted price
- `confidence_score` - Confidence level (0-100)
- `trend_direction` - Bullish/Bearish/Neutral
- `technical_indicators` - JSON field with indicator values
- `reasoning` - Text explanation of analysis (may be enhanced by local LLM if enabled)

### Script Status Table
- `id` - Primary key
- `script_name` - Name of script (collector/analyzer)
- `last_run` - Last execution timestamp
- `status` - Running/Success/Error
- `message` - Status message or error details
- `next_run` - Scheduled next execution time

## Environment Variables

Create a `.env` file with:

```env
# Database (for Docker, these are used by docker-compose)
DB_USER=dogeanalyze
DB_PASSWORD=dogeanalyze_pass
DB_NAME=dogeanalyze
DB_PORT=5432

# Database URL (for local development)
# For SQLite:
# DATABASE_URL=sqlite:///dogeanalyze.db
# For PostgreSQL (Docker):
DATABASE_URL=postgresql://dogeanalyze:dogeanalyze_pass@db:5432/dogeanalyze
# For PostgreSQL (local):
# DATABASE_URL=postgresql://user:password@localhost:5432/dogeanalyze

# API Keys (if needed)
COINGECKO_API_KEY=
CRYPTOCOMPARE_API_KEY=

# Collection Settings
COLLECTION_INTERVAL_MINUTES=5
ANALYSIS_INTERVAL_MINUTES=15

# Dashboard
FLASK_APP=dashboard.app
FLASK_ENV=production
FLASK_PORT=5000
SECRET_KEY=your-secret-key-here

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/dogeanalyze.log

# Local LLM Model Configuration (e.g., LM Studio)
# Set LOCAL_MODEL_ENABLED=true to enable local model analysis
LOCAL_MODEL_ENABLED=false
# URL of your local LLM server (LM Studio default: http://127.0.0.1:1234)
LOCAL_MODEL_URL=http://127.0.0.1:1234
# Request timeout in seconds
LOCAL_MODEL_TIMEOUT=30
# Temperature for model responses (0.0-1.0, lower = more focused)
LOCAL_MODEL_TEMPERATURE=0.7
# Maximum tokens in response
LOCAL_MODEL_MAX_TOKENS=500
```

## Getting Started

### Option 1: Docker (Recommended)

**Prerequisites:**
- Docker Engine 20.10+
- Docker Compose 2.0+

**Quick Start:**
1. Clone the repository
2. Create `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your settings (optional)
   ```
3. Start all services:
   ```bash
   # Using Make (recommended)
   make up
   
   # Or using docker-compose directly
   docker-compose up -d
   ```
4. Access dashboard at `http://localhost:5000`

**Useful Commands:**
```bash
# View logs
make logs                    # All services
make logs-collector          # Collector only
make logs-analyzer           # Analyzer only
make logs-dashboard          # Dashboard only

# Container management
make ps                      # Show container status
make restart                 # Restart all services
make down                    # Stop all services

# Database operations
make backup-db               # Backup database
make shell-db                # Access database shell

# See all commands
make help
```

See [DOCKER.md](DOCKER.md) for detailed Docker documentation.

### Option 2: Local Development

**Prerequisites:**
- Python 3.11 or higher
- pip package manager
- PostgreSQL (required for production, can use SQLite for development with modifications)

**Installation:**

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure

5. Initialize database:
   ```bash
   python -m database.db_manager init
   ```

6. Run data collector:
   ```bash
   python -m collector.scheduler
   ```

7. Run analysis bot:
   ```bash
   python -m analyzer.predictor
   ```

8. Start dashboard:
   ```bash
   python -m dashboard.app
   ```

## Usage

### Data Collector
The collector script runs continuously, fetching data at configured intervals and storing it in the database.

### Analysis Bot
The analysis bot processes recent market data and generates predictions for different timeframes. 
The timeframes include:
- **Dynamic interval timeframe** - Based on `ANALYSIS_INTERVAL_MINUTES` (e.g., if set to 10, creates "10m" predictions)
- **Standard timeframes**: 1h, 4h, 24h, 7d, 30d

For example, if `ANALYSIS_INTERVAL_MINUTES=10`, the bot will generate predictions for: 10m, 1h, 4h, 24h, 7d, 30d

#### Local LLM Model Integration (Optional)
The analyzer supports integration with local LLM models (e.g., LM Studio) for enhanced analysis:

1. **Start your local LLM server** (e.g., LM Studio on `http://127.0.0.1:1234`)
2. **Enable in `.env` file**:
   ```env
   LOCAL_MODEL_ENABLED=true
   LOCAL_MODEL_URL=http://127.0.0.1:1234
   ```
3. **Restart the analyzer** - it will automatically use the local model for deeper analysis

When enabled, the analyzer will:
- Generate enhanced reasoning using the local LLM
- Provide deeper market insights and context
- Combine technical analysis with AI-powered interpretation
- Fall back to basic analysis if the model is unavailable

**Logging**: All AI requests are comprehensively logged with:
- Request/response timing and sizes
- Token usage (if available from the API)
- Error details and fallback behavior
- Model availability checks
- Enhanced vs basic analysis indicators

Check logs with: `docker-compose logs -f analyzer` or `make logs-analyzer`

### Dashboard
Access the web interface at `http://localhost:5000` (or configured port) to view:
- Real-time Dogecoin price and metrics
- Historical price charts (24h, 7d, 30d views)
- Analysis predictions for 1h, 4h, 24h, 7d, 30d timeframes
- Script status and health monitoring
- Dashboard statistics and trends

## API Endpoints

All endpoints return JSON responses:

- `GET /api/health` - Health check endpoint
  - Returns: `{status: "healthy|unhealthy", timestamp: "..."}`
  
- `GET /api/current` - Get current market data (latest entry)
  - Returns: Latest market data object
  
- `GET /api/history?hours=24&limit=100` - Get historical market data
  - Parameters:
    - `hours` (optional, default: 24) - Number of hours of history
    - `limit` (optional, default: 100) - Maximum number of records
  - Returns: `{data: [...], count: N, hours: N}`
  
- `GET /api/analysis?timeframe=1h` - Get latest analysis results (one per timeframe)
  - Parameters:
    - `timeframe` (optional) - Filter by timeframe (1h, 4h, 24h, 7d, 30d)
  - Returns: `{data: [...], by_timeframe: {...}}`
  - Note: Returns only the most recent analysis for each timeframe
  
- `GET /api/analysis/history` - Get prediction history (all historical predictions)
  - Parameters:
    - `timeframe` (optional) - Filter by specific timeframe (1h, 4h, 24h, 7d, 30d)
    - `limit` (optional, default: 100, max: 1000) - Maximum number of records to return
    - `hours` (optional) - Filter by time range (e.g., 168 for last 7 days)
  - Returns: `{data: [...], count: N, by_timeframe: {...}, timeframe: "...", limit: N, hours: N}`
  - Example: `/api/analysis/history?timeframe=24h&limit=50&hours=168` - Last 50 predictions for 24h timeframe in the past 7 days
  
- `GET /api/status` - Get script statuses
  - Returns: `{data: [...], count: N}`
  
- `GET /api/stats` - Get dashboard statistics
  - Returns: `{current_price, price_change_24h, total_data_points, total_analyses, last_update}`

## Contributing

1. Follow PEP 8 style guidelines
2. Write tests for new features
3. Update documentation as needed
4. Use meaningful commit messages

## License

[To be determined]

## Additional Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for both Docker and local development
- **[DOCKER.md](DOCKER.md)** - Comprehensive Docker setup and troubleshooting guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture and container design
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Original project plan and implementation details
- **[collector/README.md](collector/README.md)** - Data collector module documentation

## Future Enhancements

- Machine learning models for price prediction
- Email/SMS alerts for significant price movements
- Support for multiple cryptocurrencies
- Advanced charting with technical indicators overlay
- Backtesting framework for analysis strategies
- WebSocket support for real-time dashboard updates
- CI/CD pipeline
- Kubernetes deployment manifests
- Performance metrics and monitoring dashboard

