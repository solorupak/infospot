# Makefile for InfoSpot Django Project
# Usage: make <command>

# Default environment
COMPOSE_FILE_LOCAL = docker-compose.local.yml
COMPOSE_FILE_PROD = docker-compose.production.yml

# Auto-detect Docker Compose command
DOCKER_COMPOSE := $(shell command -v docker-compose 2> /dev/null)
ifndef DOCKER_COMPOSE
	DOCKER_COMPOSE := docker compose
else
	DOCKER_COMPOSE := docker-compose
endif

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help build up down restart logs shell manage test migrate makemigrations collectstatic createsuperuser clean prune add-package remove-package sync-packages lock-packages show-packages show-outdated add-dev-package remove-dev-package install-package update-package install-requirements update-requirements pkg-install pkg-remove pkg-update pkg-list pkg-outdated check-docker

# Default target
help: ## Show this help message
	@echo "$(GREEN)InfoSpot Django Project - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# Docker Commands
build: ## Build all containers
	@echo "$(GREEN)Building containers...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) build

build-prod: ## Build production containers
	@echo "$(GREEN)Building production containers...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_PROD) build

up: ## Start all containers in detached mode
	@echo "$(GREEN)Starting containers...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) up -d --remove-orphans

up-prod: ## Start production containers
	@echo "$(GREEN)Starting production containers...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_PROD) up -d --remove-orphans

down: ## Stop all containers
	@echo "$(YELLOW)Stopping containers...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) down

down-prod: ## Stop production containers
	@echo "$(YELLOW)Stopping production containers...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_PROD) down

restart: ## Restart all containers
	@echo "$(YELLOW)Restarting containers...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) restart

logs: ## View logs from all containers
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) logs -f

logs-django: ## View Django container logs
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) logs -f django

logs-postgres: ## View PostgreSQL container logs
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) logs -f postgres

logs-redis: ## View Redis container logs
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) logs -f redis

logs-celery: ## View Celery worker logs
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) logs -f celeryworker

# Django Management Commands
shell: ## Open Django shell
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py shell

shell-plus: ## Open Django shell_plus (if available)
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py shell_plus

bash: ## Open bash shell in Django container
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django bash

manage: ## Run Django management command (usage: make manage cmd="command")
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py $(cmd)

# Database Commands
migrate: ## Run database migrations
	@echo "$(GREEN)Running migrations...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py migrate

makemigrations: ## Create new migrations
	@echo "$(GREEN)Creating migrations...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py makemigrations

showmigrations: ## Show migration status
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py showmigrations

dbshell: ## Open database shell
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py dbshell

# User Management
createsuperuser: ## Create Django superuser
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py createsuperuser

# Static Files
collectstatic: ## Collect static files
	@echo "$(GREEN)Collecting static files...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py collectstatic --noinput

# Testing
test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django python manage.py test

test-coverage: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django coverage run --source='.' manage.py test
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django coverage report

pytest: ## Run pytest
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django pytest

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

# Package Management Commands (using uv)
add-package: ## Add a package (usage: make add-package pkg="package-name")
	@if [ -z "$(pkg)" ]; then \
		echo "$(RED)Error: Package name required. Usage: make add-package pkg=\"package-name\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Adding package: $(pkg)$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv add $(pkg)
	@echo "$(GREEN)Package $(pkg) added successfully$(NC)"

remove-package: ## Remove a package (usage: make remove-package pkg="package-name")
	@if [ -z "$(pkg)" ]; then \
		echo "$(RED)Error: Package name required. Usage: make remove-package pkg=\"package-name\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Removing package: $(pkg)$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv remove $(pkg)
	@echo "$(GREEN)Package $(pkg) removed$(NC)"

sync-packages: ## Sync packages with pyproject.toml
	@echo "$(GREEN)Syncing packages with pyproject.toml...$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv sync
	@echo "$(GREEN)Packages synced$(NC)"

lock-packages: ## Update uv.lock file
	@echo "$(GREEN)Updating uv.lock file...$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv lock
	@echo "$(GREEN)Lock file updated$(NC)"

show-packages: ## Show currently installed packages
	@echo "$(GREEN)Currently installed packages:$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv pip list

show-outdated: ## Show outdated packages
	@echo "$(GREEN)Checking for outdated packages...$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv pip list --outdated

# Development dependency management
add-dev-package: ## Add a development package (usage: make add-dev-package pkg="package-name")
	@if [ -z "$(pkg)" ]; then \
		echo "$(RED)Error: Package name required. Usage: make add-dev-package pkg=\"package-name\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Adding development package: $(pkg)$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv add --group dev $(pkg)
	@echo "$(GREEN)Development package $(pkg) added successfully$(NC)"

remove-dev-package: ## Remove a development package (usage: make remove-dev-package pkg="package-name")
	@if [ -z "$(pkg)" ]; then \
		echo "$(RED)Error: Package name required. Usage: make remove-dev-package pkg=\"package-name\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Removing development package: $(pkg)$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv remove --group dev $(pkg)
	@echo "$(GREEN)Development package $(pkg) removed$(NC)"

# Legacy pip-style commands (deprecated but kept for compatibility)
install-package: ## [DEPRECATED] Use add-package instead
	@echo "$(YELLOW)Warning: install-package is deprecated. Use 'make add-package' instead$(NC)"
	@make add-package pkg="$(pkg)"

update-package: ## Update a package (usage: make update-package pkg="package-name")
	@if [ -z "$(pkg)" ]; then \
		echo "$(RED)Error: Package name required. Usage: make update-package pkg=\"package-name\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Updating package: $(pkg)$(NC)"
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv add $(pkg) --upgrade
	@echo "$(GREEN)Package $(pkg) updated$(NC)"

install-requirements: ## [DEPRECATED] Use sync-packages instead
	@echo "$(YELLOW)Warning: install-requirements is deprecated. Use 'make sync-packages' instead$(NC)"
	@make sync-packages

update-requirements: ## [DEPRECATED] Use lock-packages instead
	@echo "$(YELLOW)Warning: update-requirements is deprecated. Use 'make lock-packages' instead$(NC)"
	@make lock-packages

# Advanced Package Management (using manage_packages.py script)
pkg-install: ## Install package with script (usage: make pkg-install pkg="package-name" ver="version")
	@if [ -z "$(pkg)" ]; then \
		echo "$(RED)Error: Package name required. Usage: make pkg-install pkg=\"package-name\" [ver=\"version\"]$(NC)"; \
		exit 1; \
	fi
	@if [ -n "$(ver)" ]; then \
		$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv add $(pkg)==$(ver); \
	else \
		$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv add $(pkg); \
	fi

pkg-remove: ## Remove package with script (usage: make pkg-remove pkg="package-name")
	@if [ -z "$(pkg)" ]; then \
		echo "$(RED)Error: Package name required. Usage: make pkg-remove pkg=\"package-name\"$(NC)"; \
		exit 1; \
	fi
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv remove $(pkg)

pkg-update: ## Update package with script (usage: make pkg-update pkg="package-name")
	@if [ -z "$(pkg)" ]; then \
		echo "$(RED)Error: Package name required. Usage: make pkg-update pkg=\"package-name\"$(NC)"; \
		exit 1; \
	fi
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv add $(pkg) --upgrade

pkg-list: ## List packages with script
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv pip list

pkg-outdated: ## Show outdated packages with script
	@$(DOCKER_COMPOSE) -f $(COMPOSE_FILE_LOCAL) exec django uv pip list --outdated
check-docker: ## Check Docker and Docker Compose versions
	@echo "$(GREEN)Docker version:$(NC)"
	@docker --version
	@echo "$(GREEN)Docker Compose command: $(DOCKER_COMPOSE)$(NC)"
	@$(DOCKER_COMPOSE) --version