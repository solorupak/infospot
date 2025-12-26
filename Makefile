# Makefile for InfoSpot Django Project
# Usage: make <command>

# Default environment
COMPOSE_FILE_LOCAL = docker-compose.local.yml
COMPOSE_FILE_PROD = docker-compose.production.yml

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help build up down restart logs shell manage test migrate makemigrations collectstatic createsuperuser clean prune

# Default target
help: ## Show this help message
	@echo "$(GREEN)InfoSpot Django Project - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# Docker Commands
build: ## Build all containers
	@echo "$(GREEN)Building containers...$(NC)"
	docker compose -f $(COMPOSE_FILE_LOCAL) build

build-prod: ## Build production containers
	@echo "$(GREEN)Building production containers...$(NC)"
	docker compose -f $(COMPOSE_FILE_PROD) build

up: ## Start all containers in detached mode
	@echo "$(GREEN)Starting containers...$(NC)"
	docker compose -f $(COMPOSE_FILE_LOCAL) up -d --remove-orphans

up-prod: ## Start production containers
	@echo "$(GREEN)Starting production containers...$(NC)"
	docker compose -f $(COMPOSE_FILE_PROD) up -d --remove-orphans

down: ## Stop all containers
	@echo "$(YELLOW)Stopping containers...$(NC)"
	docker compose -f $(COMPOSE_FILE_LOCAL) down

down-prod: ## Stop production containers
	@echo "$(YELLOW)Stopping production containers...$(NC)"
	docker compose -f $(COMPOSE_FILE_PROD) down

restart: ## Restart all containers
	@echo "$(YELLOW)Restarting containers...$(NC)"
	docker compose -f $(COMPOSE_FILE_LOCAL) restart

logs: ## View logs from all containers
	docker compose -f $(COMPOSE_FILE_LOCAL) logs -f

logs-django: ## View Django container logs
	docker compose -f $(COMPOSE_FILE_LOCAL) logs -f django

logs-postgres: ## View PostgreSQL container logs
	docker compose -f $(COMPOSE_FILE_LOCAL) logs -f postgres

logs-redis: ## View Redis container logs
	docker compose -f $(COMPOSE_FILE_LOCAL) logs -f redis

logs-celery: ## View Celery worker logs
	docker compose -f $(COMPOSE_FILE_LOCAL) logs -f celeryworker

# Django Management Commands
shell: ## Open Django shell
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py shell

shell-plus: ## Open Django shell_plus (if available)
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py shell_plus

bash: ## Open bash shell in Django container
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django bash

manage: ## Run Django management command (usage: make manage cmd="command")
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py $(cmd)

# Database Commands
migrate: ## Run database migrations
	@echo "$(GREEN)Running migrations...$(NC)"
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py migrate

makemigrations: ## Create new migrations
	@echo "$(GREEN)Creating migrations...$(NC)"
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py makemigrations

showmigrations: ## Show migration status
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py showmigrations

dbshell: ## Open database shell
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py dbshell

# User Management
createsuperuser: ## Create Django superuser
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py createsuperuser

# Static Files
collectstatic: ## Collect static files
	@echo "$(GREEN)Collecting static files...$(NC)"
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py collectstatic --noinput

# Testing
test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django python manage.py test

test-coverage: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django coverage run --source='.' manage.py test
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django coverage report

pytest: ## Run pytest
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django pytest

# Development Setup
setup: build up migrate createsuperuser ## Complete development setup
	@echo "$(GREEN)Development environment setup complete!$(NC)"

setup-quick: build up migrate ## Quick setup without superuser
	@echo "$(GREEN)Quick development setup complete!$(NC)"

# Maintenance Commands
clean: ## Remove stopped containers and unused images
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	docker container prune -f
	docker image prune -f

prune: ## Remove all containers, volumes, and images (DESTRUCTIVE)
	@echo "$(RED)WARNING: This will remove all containers, volumes, and images!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose -f $(COMPOSE_FILE_LOCAL) down -v --remove-orphans; \
		docker system prune -af --volumes; \
	fi

reset-db: ## Reset database (DESTRUCTIVE)
	@echo "$(RED)WARNING: This will delete all database data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose -f $(COMPOSE_FILE_LOCAL) down; \
		docker volume rm infospot_local_postgres_data || true; \
		docker compose -f $(COMPOSE_FILE_LOCAL) up -d postgres; \
		sleep 5; \
		make migrate; \
	fi

# Celery Commands
celery-worker: ## Start Celery worker (foreground)
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django celery -A config.celery_app worker --loglevel=info

celery-beat: ## Start Celery beat (foreground)
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django celery -A config.celery_app beat --loglevel=info

celery-flower: ## Open Flower monitoring (already running on port 5555)
	@echo "$(GREEN)Flower is running at http://localhost:5555$(NC)"

# Utility Commands
ps: ## Show running containers
	docker compose -f $(COMPOSE_FILE_LOCAL) ps

top: ## Show container processes
	docker compose -f $(COMPOSE_FILE_LOCAL) top

exec: ## Execute command in Django container (usage: make exec cmd="command")
	docker compose -f $(COMPOSE_FILE_LOCAL) exec django $(cmd)

# Mail Commands
mailpit: ## Open Mailpit interface (already running on port 8025)
	@echo "$(GREEN)Mailpit is running at http://localhost:8025$(NC)"

# Quick shortcuts
dev: up ## Alias for 'up' - start development environment
stop: down ## Alias for 'down' - stop containers
rebuild: down build up ## Rebuild and restart containers