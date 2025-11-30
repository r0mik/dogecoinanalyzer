# DogeAnalyze Container Architecture

## Container Overview

The project uses **4 separate Docker containers**:

1. **db** - PostgreSQL Database
2. **collector** - Data Collection Service
3. **analyzer** - Analysis Bot Service
4. **dashboard** - Web Dashboard Service

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                            │
│                  (dogeanalyze-network)                      │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   collector  │      │   analyzer   │                    │
│  │  (Container) │      │  (Container) │                    │
│  │              │      │              │                    │
│  │ - Fetches    │      │ - Technical  │                    │
│  │   Dogecoin   │      │   Analysis   │                    │
│  │   data       │      │ - Predictions│                    │
│  │ - Every 5min │      │ - Every 15min│                    │
│  └──────┬───────┘      └──────┬───────┘                    │
│         │                     │                             │
│         │                     │                             │
│         └──────────┬──────────┘                             │
│                    │                                         │
│                    ▼                                         │
│         ┌─────────────────────┐                             │
│         │         db           │                             │
│         │   (PostgreSQL 15)    │                             │
│         │                      │                             │
│         │ - market_data        │                             │
│         │ - analysis_results   │                             │
│         │ - script_status      │                             │
│         └──────────┬───────────┘                             │
│                    │                                         │
│                    │                                         │
│         ┌──────────▼───────────┐                             │
│         │     dashboard        │                             │
│         │    (Container)       │                             │
│         │                      │                             │
│         │ - Flask Web App      │                             │
│         │ - Port 5000          │                             │
│         │ - API Endpoints      │                             │
│         │ - Web Interface      │                             │
│         └──────────────────────┘                             │
│                    │                                         │
│                    │ (Exposed to host)                       │
└────────────────────┼─────────────────────────────────────────┘
                     │
                     ▼
            http://localhost:5000
```

## Container Details

### 1. Database Container (db)

- **Image**: `postgres:15-alpine`
- **Purpose**: Stores all application data
- **Port**: 5432 (mapped to host)
- **Volume**: `postgres_data` (persistent storage)
- **Health Check**: PostgreSQL readiness check
- **Initialization**: Auto-runs `database/init.sql` on first start

**Tables:**
- `market_data` - Raw Dogecoin market data
- `analysis_results` - Analysis predictions
- `script_status` - Service status tracking

### 2. Collector Container

- **Base Image**: `python:3.11-slim`
- **Purpose**: Fetches Dogecoin data from free APIs
- **Schedule**: Runs every 5 minutes (configurable)
- **Dependencies**: Waits for `db` to be healthy
- **Logs**: Mounted to `./logs` on host
- **Networks**: `dogeanalyze-network`

**Functionality:**
- Connects to CoinGecko, CryptoCompare, Binance APIs
- Fetches price, volume, market cap data
- Stores data in `market_data` table
- Updates `script_status` table

### 3. Analyzer Container

- **Base Image**: `python:3.11-slim`
- **Purpose**: Performs technical analysis and generates predictions
- **Schedule**: Runs every 15 minutes (configurable)
- **Dependencies**: Requires `db` and `collector` services
- **Logs**: Mounted to `./logs` on host
- **Networks**: `dogeanalyze-network`

**Functionality:**
- Reads historical data from `market_data` table
- Calculates technical indicators (RSI, MACD, etc.)
- Generates predictions for 1h, 4h, 24h timeframes
- Stores results in `analysis_results` table
- Updates `script_status` table

### 4. Dashboard Container

- **Base Image**: `python:3.11-slim`
- **Purpose**: Web interface for monitoring and visualization
- **Port**: 5000 (mapped to host)
- **Dependencies**: Requires `db` service
- **Logs**: Mounted to `./logs` on host
- **Networks**: `dogeanalyze-network`

**Functionality:**
- Flask web application
- REST API endpoints
- Real-time data display
- Script status monitoring
- Analysis results visualization

## Network Architecture

All containers communicate through a **bridge network** (`dogeanalyze-network`):

- Containers can reach each other using service names
- Database accessible at `db:5432` from other containers
- No external network access required (except for API calls)
- Only dashboard port (5000) is exposed to host

## Data Flow

```
1. Collector fetches data from external APIs
   ↓
2. Data stored in PostgreSQL (market_data table)
   ↓
3. Analyzer reads market_data, performs analysis
   ↓
4. Analysis results stored in PostgreSQL (analysis_results table)
   ↓
5. Dashboard reads from both tables via API
   ↓
6. Dashboard displays data to users via web interface
```

## Volume Management

### Persistent Volumes

- **postgres_data**: Database files (survives container restarts)
  - Location: Docker managed volume
  - Backup: Use `make backup-db` or `docker-compose exec db pg_dump`

### Bind Mounts

- **./logs**: Application logs (shared across containers)
  - Location: `./logs` directory on host
  - Purpose: Centralized log storage

## Service Dependencies

```
db (PostgreSQL)
  ↑
  ├── collector (waits for db health check)
  ├── analyzer (waits for db health check + collector started)
  └── dashboard (waits for db health check)
```

**Startup Order:**
1. `db` starts first and becomes healthy
2. `collector` starts after db is healthy
3. `analyzer` starts after db is healthy and collector is running
4. `dashboard` starts after db is healthy

## Resource Requirements

**Minimum:**
- 2 CPU cores
- 2GB RAM
- 5GB disk space

**Recommended:**
- 4 CPU cores
- 4GB RAM
- 10GB disk space

## Scaling Considerations

- **Database**: Can be moved to external managed PostgreSQL
- **Collector**: Can run multiple instances (with coordination)
- **Analyzer**: Can run multiple instances (with coordination)
- **Dashboard**: Can scale horizontally behind load balancer

## Security Considerations

- Database password should be changed in production
- Flask SECRET_KEY must be set to random value
- Consider using Docker secrets for sensitive data
- Network isolation (containers only communicate internally)
- Only dashboard port exposed to host

## Monitoring

Each container logs to:
- Container stdout/stderr (viewable via `docker-compose logs`)
- Shared log directory (`./logs` on host)

Health checks:
- Database: PostgreSQL readiness
- Other services: Can be extended with custom endpoints

