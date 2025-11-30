# Docker Setup Guide

## Overview

DogeAnalyze uses Docker Compose to orchestrate multiple containers:

1. **db** - PostgreSQL database
2. **collector** - Data collection service
3. **analyzer** - Analysis bot service
4. **dashboard** - Web dashboard service

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

1. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Build and start all containers**
   ```bash
   # Using Make (recommended)
   make up
   
   # Or using docker-compose directly
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   # All services
   make logs
   # Or: docker-compose logs -f
   
   # Specific service
   make logs-dashboard
   make logs-collector
   make logs-analyzer
   ```

4. **Access dashboard**
   Open browser to: `http://localhost:5000`

**Tip:** Use `make help` to see all available commands.

## Container Details

### Database Container (db)
- **Image**: `postgres:15-alpine`
- **Port**: 5432 (mapped to host)
- **Volume**: `postgres_data` (persistent storage)
- **Health Check**: Automatic PostgreSQL readiness check
- **Initialization**: Runs `database/init.sql` on first start

### Collector Container
- **Purpose**: Fetches Dogecoin data from APIs
- **Schedule**: Runs every 5 minutes (configurable)
- **Dependencies**: Waits for database to be healthy
- **Logs**: Mounted to `./logs` directory

### Analyzer Container
- **Purpose**: Performs technical analysis and generates predictions
- **Schedule**: Runs every 15 minutes (configurable)
- **Dependencies**: Database and collector service
- **Logs**: Mounted to `./logs` directory

### Dashboard Container
- **Purpose**: Web interface for monitoring and visualization
- **Port**: 5000 (mapped to host)
- **Dependencies**: Database service
- **Logs**: Mounted to `./logs` directory

## Docker Commands

### Using Makefile (Recommended)

The project includes a `Makefile` with convenient shortcuts:

```bash
make help          # Show all available commands
make build         # Build all images
make up            # Start all services
make down          # Stop all services
make logs          # View all logs
make ps            # Show container status
make rebuild       # Rebuild and restart
make clean         # Remove everything
```

### Direct Docker Compose Commands

### Start Services
```bash
# Start all services in detached mode
docker-compose up -d
# Or: make up

# Start specific service
docker-compose up -d dashboard
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes database)
docker-compose down -v
```

### View Status
```bash
# List running containers
docker-compose ps

# View resource usage
docker stats
```

### View Logs
```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f collector

# Last 100 lines
docker-compose logs --tail=100 dashboard
```

### Rebuild Containers
```bash
# Rebuild all containers
docker-compose build

# Rebuild specific service
docker-compose build dashboard

# Rebuild and restart
docker-compose up -d --build
```

### Execute Commands in Containers
```bash
# Access database
docker-compose exec db psql -U dogeanalyze -d dogeanalyze

# Access collector container shell
docker-compose exec collector /bin/bash

# Run Python script in container
docker-compose exec dashboard python -m utils.helpers
```

### Database Operations
```bash
# Backup database
docker-compose exec db pg_dump -U dogeanalyze dogeanalyze > backup.sql

# Restore database
docker-compose exec -T db psql -U dogeanalyze dogeanalyze < backup.sql

# View database logs
docker-compose logs db
```

## Environment Variables

All environment variables are configured in `.env` file. Key variables:

- `DB_USER` - PostgreSQL username (default: dogeanalyze)
- `DB_PASSWORD` - PostgreSQL password (default: dogeanalyze_pass)
- `DB_NAME` - Database name (default: dogeanalyze)
- `DB_PORT` - Database port mapping (default: 5432)
- `COLLECTION_INTERVAL_MINUTES` - Data collection frequency (default: 5)
- `ANALYSIS_INTERVAL_MINUTES` - Analysis frequency (default: 15)
- `FLASK_PORT` - Dashboard port (default: 5000)
- `SECRET_KEY` - Flask secret key (change in production!)

## Development Mode

For development with hot-reload:

1. **Create override file**
   ```bash
   cp docker-compose.override.yml.example docker-compose.override.yml
   ```

2. **Start with override**
   ```bash
   docker-compose up
   ```

The override file mounts source code directories, enabling live code changes without rebuilding.

## Production Considerations

1. **Change default passwords** in `.env`
2. **Set strong SECRET_KEY** for Flask
3. **Use external PostgreSQL** for production (update DATABASE_URL)
4. **Configure reverse proxy** (nginx/traefik) for dashboard
5. **Set up log rotation** for persistent logs
6. **Use Docker secrets** for sensitive data
7. **Configure resource limits** in docker-compose.yml
8. **Set up monitoring** (Prometheus, Grafana)
9. **Enable health checks** (already configured)
10. **Use Docker Swarm or Kubernetes** for orchestration

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs <service-name>

# Check container status
docker-compose ps

# Restart service
docker-compose restart <service-name>
```

### Database connection issues
```bash
# Verify database is healthy
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec db pg_isready -U dogeanalyze
```

### Port already in use
```bash
# Change port in .env file
FLASK_PORT=5001
DB_PORT=5433

# Recreate containers
docker-compose up -d --force-recreate
```

### Out of disk space
```bash
# Clean up unused Docker resources
docker system prune -a

# Remove old volumes (⚠️ deletes data)
docker volume prune
```

### Rebuild after code changes
```bash
# Rebuild and restart
docker-compose up -d --build

# Or rebuild specific service
docker-compose up -d --build dashboard
```

## Network Architecture

All containers are on the `dogeanalyze-network` bridge network:
- Containers can communicate using service names (e.g., `db`, `dashboard`)
- Database is accessible at `db:5432` from other containers
- Dashboard is accessible at `dashboard:5000` from other containers
- External access only through mapped ports

## Volume Management

- **postgres_data**: Persistent database storage
- **./logs**: Shared log directory (mounted from host)

To backup volumes:
```bash
docker run --rm -v dogeanalyze_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Health Checks

All services include health checks:
- **db**: PostgreSQL readiness check
- **collector/analyzer/dashboard**: Can be extended with custom health endpoints

View health status:
```bash
docker-compose ps
```

