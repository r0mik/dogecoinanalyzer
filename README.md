# DogeAnalyze - Dogecoin Data Collection & Analysis Platform

## Project Overview

DogeAnalyze is a comprehensive platform for collecting, analyzing, and visualizing Dogecoin market data. The system consists of:

1. **Data Collector Script** - Fetches real-time Dogecoin data (price, volume, market cap, etc.) from free APIs
2. **Analysis Bot** - Performs technical analysis and generates predictions for 1h, 4h, and 24h timeframes
3. **Web Dashboard** - Displays real-time data, script statuses, and analysis results

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

## Working Plan

### Phase 1: Project Setup & Infrastructure
- [x] Create project structure
- [ ] Set up Python virtual environment
- [ ] Initialize database schema
- [ ] Configure environment variables
- [ ] Set up logging system

### Phase 2: Data Collector Script
- [ ] Research and select free Dogecoin data APIs (CoinGecko, CryptoCompare, Binance API)
- [ ] Implement data fetching module
- [ ] Create database models for raw market data
- [ ] Implement scheduled data collection (cron-like or scheduler)
- [ ] Add error handling and retry logic
- [ ] Add data validation

### Phase 3: Analysis Bot
- [ ] Implement technical indicators (RSI, MACD, Moving Averages, Bollinger Bands)
- [ ] Create prediction models for 1h, 4h, 24h timeframes
- [ ] Design database schema for analysis results
- [ ] Implement analysis execution logic
- [ ] Add confidence scoring for predictions
- [ ] Schedule periodic analysis runs

### Phase 4: Web Dashboard
- [ ] Set up web framework (Flask or FastAPI)
- [ ] Create API endpoints for:
  - Current market data
  - Historical data
  - Analysis results
  - Script statuses
- [ ] Build frontend dashboard with:
  - Real-time price charts
  - Script status indicators
  - Analysis results display
  - Historical data visualization
- [ ] Add WebSocket support for real-time updates (optional)

### Phase 5: Integration & Testing
- [ ] Integrate all components
- [ ] Test data collection reliability
- [ ] Validate analysis accuracy
- [ ] Test dashboard functionality
- [ ] Add monitoring and alerting

### Phase 6: Deployment & Documentation
- [ ] Create deployment scripts
- [ ] Write API documentation
- [ ] Add usage examples
- [ ] Create user guide

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
│   └── models.py
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
│   ├── logger.py
│   └── helpers.py
└── tests/
    ├── test_collector.py
    ├── test_analyzer.py
    └── test_dashboard.py
```

## Technology Stack

### Backend
- **Python 3.9+** - Main programming language
- **SQLAlchemy** - ORM for database operations
- **SQLite/PostgreSQL** - Database (SQLite for dev, PostgreSQL for production)
- **Flask/FastAPI** - Web framework for dashboard
- **APScheduler** - Task scheduling for data collection and analysis
- **Requests** - HTTP client for API calls
- **Pandas** - Data manipulation for analysis
- **NumPy** - Numerical computations

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
- `timeframe` - Prediction timeframe (1h, 4h, 24h)
- `predicted_price` - Predicted price
- `confidence_score` - Confidence level (0-100)
- `trend_direction` - Bullish/Bearish/Neutral
- `technical_indicators` - JSON field with indicator values
- `reasoning` - Text explanation of analysis

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
   docker-compose up -d
   ```
4. Access dashboard at `http://localhost:5000`

**View logs:**
```bash
docker-compose logs -f
```

See [DOCKER.md](DOCKER.md) for detailed Docker documentation.

### Option 2: Local Development

**Prerequisites:**
- Python 3.9 or higher
- pip package manager
- PostgreSQL (or use SQLite for development)

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

### Dashboard
Access the web interface at `http://localhost:5000` (or configured port) to view:
- Real-time Dogecoin price and metrics
- Historical price charts
- Analysis predictions for 1h, 4h, 24h
- Script status and health monitoring

## API Endpoints (Planned)

- `GET /api/current` - Get current market data
- `GET /api/history?hours=24` - Get historical data
- `GET /api/analysis?timeframe=1h` - Get analysis results
- `GET /api/status` - Get script statuses
- `GET /api/health` - Health check endpoint

## Contributing

1. Follow PEP 8 style guidelines
2. Write tests for new features
3. Update documentation as needed
4. Use meaningful commit messages

## License

[To be determined]

## Future Enhancements

- Machine learning models for price prediction
- Email/SMS alerts for significant price movements
- Support for multiple cryptocurrencies
- Advanced charting with technical indicators overlay
- Backtesting framework for analysis strategies
- REST API for external integrations
- CI/CD pipeline
- Kubernetes deployment manifests

