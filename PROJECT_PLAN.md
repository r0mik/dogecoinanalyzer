# DogeAnalyze - Detailed Project Plan

## Project Goals

1. **Data Collection**: Automatically fetch Dogecoin market data from free APIs
2. **Price Analysis**: Generate technical analysis and predictions for 1h, 4h, 24h timeframes
3. **Dashboard**: Web interface to monitor scripts and view analysis results

## Implementation Details

### 1. Data Collector Script

#### Free API Sources
- **CoinGecko API** (https://www.coingecko.com/api/documentations/v3)
  - Free tier: 10-50 calls/minute
  - Endpoint: `/simple/price?ids=dogecoin&vs_currencies=usd&include_24hr_change=true`
  - No API key required for basic usage

- **CryptoCompare API** (https://min-api.cryptocompare.com/)
  - Free tier: 100,000 calls/month
  - Endpoint: `/data/price?fsym=DOGE&tsyms=USD`
  - No API key required

- **Binance Public API** (https://binance-docs.github.io/apidocs/spot/en/)
  - Free, no authentication needed
  - Endpoint: `/api/v3/ticker/24hr?symbol=DOGEUSDT`

#### Data to Collect
- Current price (USD)
- 24h volume
- Market cap
- 24h price change (%)
- 24h high/low
- Last update timestamp

#### Implementation Steps
1. Create API client classes for each source
2. Implement data fetching with error handling
3. Add rate limiting to respect API limits
4. Store data in database with timestamp
5. Implement scheduler to run every 5 minutes (configurable)
6. Add logging for monitoring

### 2. Analysis Bot

#### Technical Indicators to Implement
- **RSI (Relative Strength Index)** - Momentum oscillator (14 period)
- **MACD (Moving Average Convergence Divergence)** - Trend-following indicator
- **SMA (Simple Moving Average)** - 20, 50, 200 periods
- **EMA (Exponential Moving Average)** - 12, 26 periods
- **Bollinger Bands** - Volatility indicator
- **Volume Analysis** - Compare current vs average volume

#### Prediction Logic
For each timeframe (1h, 4h, 24h):
1. Calculate all technical indicators
2. Analyze trend direction (bullish/bearish/neutral)
3. Generate price prediction based on:
   - Current trend
   - Support/resistance levels
   - Volume patterns
   - Historical patterns
4. Calculate confidence score (0-100)
5. Generate reasoning text explaining the prediction

#### Implementation Steps
1. Implement technical indicator calculations
2. Create prediction model/algorithm
3. Design analysis result storage schema
4. Schedule analysis runs (every 15 minutes)
5. Store results with timestamp and timeframe
6. Add confidence scoring system

### 3. Web Dashboard

#### Features
- **Real-time Price Display**
  - Current DOGE price
  - 24h change percentage
  - Volume and market cap
  - Price chart (last 24h, 7d, 30d)

- **Script Status Monitoring**
  - Data collector status (last run, next run, status)
  - Analysis bot status (last run, next run, status)
  - Health indicators (green/yellow/red)
  - Error messages if any

- **Analysis Results**
  - Display predictions for 1h, 4h, 24h
  - Show confidence scores
  - Display trend indicators
  - Show technical indicator values
  - Reasoning/explanation for each prediction

- **Historical Data**
  - Interactive price charts
  - Historical analysis results
  - Performance metrics

#### Technology Choices
- **Backend**: Flask (lightweight, easy to set up)
- **Frontend**: 
  - HTML/CSS/JavaScript
  - Chart.js for price charts
  - Bootstrap for responsive UI
- **Real-time Updates**: Polling every 5-10 seconds (or WebSocket if needed)

#### Implementation Steps
1. Set up Flask application structure
2. Create database models
3. Create API endpoints
4. Build frontend templates
5. Implement real-time data updates
6. Add error handling and user feedback
7. Style with CSS framework

## Database Design

### Tables

#### `market_data`
```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    price_usd DECIMAL(20, 8) NOT NULL,
    volume_24h DECIMAL(20, 2),
    market_cap DECIMAL(20, 2),
    price_change_24h DECIMAL(10, 4),
    high_24h DECIMAL(20, 8),
    low_24h DECIMAL(20, 8),
    source VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
```

#### `analysis_results`
```sql
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- '1h', '4h', '24h'
    predicted_price DECIMAL(20, 8),
    confidence_score INTEGER,  -- 0-100
    trend_direction VARCHAR(20),  -- 'bullish', 'bearish', 'neutral'
    technical_indicators TEXT,  -- JSON string
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_analysis_timestamp ON analysis_results(timestamp);
CREATE INDEX idx_analysis_timeframe ON analysis_results(timeframe);
```

#### `script_status`
```sql
CREATE TABLE script_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_name VARCHAR(50) NOT NULL,  -- 'collector', 'analyzer'
    last_run DATETIME,
    status VARCHAR(20),  -- 'running', 'success', 'error'
    message TEXT,
    next_run DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_script_name ON script_status(script_name);
```

## Development Phases

### Phase 1: Foundation (Week 1)
- Set up project structure
- Initialize database
- Create basic API clients
- Test data fetching from one API

### Phase 2: Data Collection (Week 1-2)
- Complete data collector implementation
- Add multiple API sources
- Implement scheduling
- Add error handling and logging

### Phase 3: Analysis Engine (Week 2-3)
- Implement technical indicators
- Create prediction algorithm
- Test analysis accuracy
- Store results in database

### Phase 4: Dashboard Backend (Week 3)
- Set up Flask application
- Create API endpoints
- Connect to database
- Test API responses

### Phase 5: Dashboard Frontend (Week 3-4)
- Design UI layout
- Implement price display
- Add charts
- Show script statuses
- Display analysis results

### Phase 6: Integration & Polish (Week 4)
- Integrate all components
- Add error handling
- Improve UI/UX
- Write documentation
- Testing and bug fixes

## Testing Strategy

1. **Unit Tests**
   - Test API clients
   - Test technical indicator calculations
   - Test prediction logic
   - Test database operations

2. **Integration Tests**
   - Test data collection flow
   - Test analysis pipeline
   - Test API endpoints

3. **Manual Testing**
   - Run scripts for extended periods
   - Verify data accuracy
   - Test dashboard functionality
   - Check error handling

## Deployment Considerations

### Development
- SQLite database
- Local Flask server
- Manual script execution or basic scheduler

### Production (Future)
- PostgreSQL database
- Gunicorn/uWSGI for Flask
- Systemd services or Docker containers
- Nginx reverse proxy
- Monitoring and alerting (e.g., Sentry)

## Risk Mitigation

1. **API Rate Limits**: Implement rate limiting and multiple API sources
2. **API Downtime**: Add fallback APIs and error handling
3. **Data Accuracy**: Validate data before storing
4. **Analysis Accuracy**: Clearly label predictions as estimates, not financial advice
5. **Database Growth**: Implement data retention policies (keep last 90 days)

## Success Metrics

- Data collection runs successfully 99%+ of the time
- Analysis generated for all timeframes every 15 minutes
- Dashboard loads in < 2 seconds
- All scripts show accurate status
- Predictions have reasonable confidence scores

