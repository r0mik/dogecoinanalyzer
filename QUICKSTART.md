# Quick Start Guide

## Option 1: Docker (Recommended - Easiest)

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+

### Setup Steps

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings (optional)
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **View logs** (optional)
   ```bash
   docker-compose logs -f
   ```

4. **Access dashboard**
   Open browser to: `http://localhost:5000`

5. **Stop services**
   ```bash
   docker-compose down
   ```

That's it! All 4 containers (database, collector, analyzer, dashboard) are running.

See [DOCKER.md](DOCKER.md) for more Docker commands and details.

## Option 2: Local Development

### Prerequisites
- Python 3.9 or higher
- pip package manager
- PostgreSQL (or use SQLite for development)

### Setup Steps

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

4. **Initialize database**
   ```bash
   python -m database.db_manager init
   ```

5. **Start data collector** (in one terminal)
   ```bash
   python -m collector.scheduler
   ```

6. **Start analysis bot** (in another terminal)
   ```bash
   python -m analyzer.predictor
   ```

7. **Start dashboard** (in a third terminal)
   ```bash
   python -m dashboard.app
   ```

8. **Access dashboard**
   Open browser to: `http://localhost:5000`

## Project Structure Overview

- `collector/` - Data fetching scripts
- `analyzer/` - Technical analysis and prediction engine
- `database/` - Database models and management
- `dashboard/` - Web interface
- `config/` - Configuration settings
- `utils/` - Helper functions
- `tests/` - Test suite

## Next Steps

1. Review `README.md` for detailed documentation
2. Check `PROJECT_PLAN.md` for implementation details
3. Start implementing Phase 1 components

