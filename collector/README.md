# Data Collector Module

## Overview

The collector module is responsible for fetching Dogecoin market data from multiple free APIs and storing it in the database. It runs on a configurable schedule (default: every 5 minutes).

## Components

### 1. API Clients (`api_clients.py`)

Implements clients for three free data sources:

- **CoinGeckoClient**: Fetches data from CoinGecko API
  - Rate limit: 50 calls/minute
  - Provides: price, 24h change, market cap
  
- **CryptoCompareClient**: Fetches data from CryptoCompare API
  - Rate limit: 100 calls/minute (conservative)
  - Provides: price, 24h change, volume, market cap, high/low
  
- **BinanceClient**: Fetches data from Binance Public API
  - Rate limit: 1200 calls/minute
  - Provides: price, 24h change, volume, high/low

All clients include:
- Rate limiting to respect API limits
- Retry logic (3 attempts with exponential backoff)
- Error handling and logging
- Request timeout (10 seconds)

### 2. Data Fetcher (`data_fetcher.py`)

The `DataFetcher` class:
- Orchestrates data collection from all API sources
- Validates fetched data before storing
- Stores data in the database
- Updates script status for monitoring
- Handles errors gracefully (continues if one source fails)

### 3. Scheduler (`scheduler.py`)

The scheduler:
- Uses APScheduler for periodic execution
- Runs initial collection on startup
- Schedules periodic collections (configurable interval)
- Handles graceful shutdown (SIGINT/SIGTERM)
- Updates script status in database
- Logs all operations

## Data Collected

For each collection, the following data is stored:

- `timestamp` - When the data was collected
- `price_usd` - Current price in USD
- `volume_24h` - 24-hour trading volume (if available)
- `market_cap` - Market capitalization (if available)
- `price_change_24h` - 24-hour price change percentage
- `high_24h` - 24-hour high price (if available)
- `low_24h` - 24-hour low price (if available)
- `source` - Which API provided the data

## Configuration

Settings are configured via environment variables (see `.env.example`):

- `COLLECTION_INTERVAL_MINUTES` - How often to collect data (default: 5)
- `COINGECKO_API_KEY` - Optional API key for CoinGecko
- `CRYPTOCOMPARE_API_KEY` - Optional API key for CryptoCompare
- `DATABASE_URL` - Database connection string
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

## Usage

### Running Locally

```bash
python -m collector.scheduler
```

### Running in Docker

The collector runs automatically when you start the Docker containers:

```bash
docker-compose up -d
```

Or start just the collector:

```bash
docker-compose up -d collector
```

### Viewing Logs

```bash
# Docker
docker-compose logs -f collector

# Local
tail -f logs/dogeanalyze.log
```

## Database Schema

Data is stored in the `market_data` table:

```sql
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    price_usd DECIMAL(20, 8) NOT NULL,
    volume_24h DECIMAL(20, 2),
    market_cap DECIMAL(20, 2),
    price_change_24h DECIMAL(10, 4),
    high_24h DECIMAL(20, 8),
    low_24h DECIMAL(20, 8),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling

The collector is designed to be resilient:

1. **API Failures**: If one API fails, others are still tried
2. **Retry Logic**: Each API client retries up to 3 times
3. **Data Validation**: Invalid data is rejected before storing
4. **Database Errors**: Errors are logged and don't crash the service
5. **Status Tracking**: All operations update the script_status table

## Monitoring

The collector updates its status in the `script_status` table:

- `last_run` - When the last collection ran
- `status` - Current status (running/success/error)
- `message` - Status message or error details
- `next_run` - When the next collection is scheduled

Query the status:

```sql
SELECT * FROM script_status WHERE script_name = 'collector';
```

Or via the dashboard API (when implemented).

## Rate Limiting

Each API client implements rate limiting to respect API limits:

- **CoinGecko**: 50 calls/minute
- **CryptoCompare**: 100 calls/minute (conservative)
- **Binance**: 1200 calls/minute

The rate limiter tracks calls within a time window and waits if necessary.

## Future Enhancements

- Add more data sources
- Implement data quality scoring
- Add data validation rules
- Store historical data snapshots
- Implement data deduplication
- Add webhook notifications for failures

