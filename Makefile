.PHONY: help build up down restart logs ps shell-db shell-collector shell-analyzer shell-dashboard clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services in detached mode
	docker-compose up -d

down: ## Stop and remove all containers
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Follow logs from all services
	docker-compose logs -f

logs-collector: ## Follow logs from collector service
	docker-compose logs -f collector

logs-analyzer: ## Follow logs from analyzer service
	docker-compose logs -f analyzer

logs-dashboard: ## Follow logs from dashboard service
	docker-compose logs -f dashboard

logs-db: ## Follow logs from database service
	docker-compose logs -f db

ps: ## Show status of all containers
	docker-compose ps

shell-db: ## Open shell in database container
	docker-compose exec db psql -U dogeanalyze -d dogeanalyze

shell-collector: ## Open shell in collector container
	docker-compose exec collector /bin/bash

shell-analyzer: ## Open shell in analyzer container
	docker-compose exec analyzer /bin/bash

shell-dashboard: ## Open shell in dashboard container
	docker-compose exec dashboard /bin/bash

rebuild: ## Rebuild and restart all services
	docker-compose up -d --build

clean: ## Remove containers, volumes, and images
	docker-compose down -v
	docker system prune -f

backup-db: ## Backup database to backup.sql
	docker-compose exec db pg_dump -U dogeanalyze dogeanalyze > backup.sql
	@echo "Database backed up to backup.sql"

restore-db: ## Restore database from backup.sql (requires backup.sql file)
	docker-compose exec -T db psql -U dogeanalyze dogeanalyze < backup.sql
	@echo "Database restored from backup.sql"

stats: ## Show resource usage of all containers
	docker stats

health: ## Check health status of all services
	docker-compose ps

