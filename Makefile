# AI Data Engineering Project Makefile

.PHONY: help install dev-install test clean build up down logs shell db-shell etl

# Default target
help:
	@echo "AI Data Engineering Project"
	@echo "=========================="
	@echo ""
	@echo "Available commands:"
	@echo "  install      Install dependencies"
	@echo "  dev-install  Install development dependencies"
	@echo "  test         Run tests"
	@echo "  clean        Clean up temporary files"
	@echo "  build        Build Docker images"
	@echo "  up           Start all services"
	@echo "  down         Stop all services"
	@echo "  logs         Show logs"
	@echo "  shell        Open shell in app container"
	@echo "  db-shell     Open PostgreSQL shell"
	@echo "  etl          Run ETL pipeline"
	@echo "  setup        Initial project setup"

# Installation
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install pytest black flake8 mypy

# Testing
test:
	python -m pytest tests/ -v

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec app bash

db-shell:
	docker-compose exec postgres psql -U postgres -d ai_data_engineering

# ETL
etl:
	docker-compose run --rm etl

# Development
dev:
	streamlit run src/web/streamlit_app.py

# Setup
setup:
	@echo "Setting up AI Data Engineering project..."
	@echo "1. Creating necessary directories..."
	mkdir -p data/raw data/processed logs
	@echo "2. Copying environment file..."
	cp env.example .env
	@echo "3. Setting up Kaggle credentials..."
	@echo "Please configure your .env file with:"
	@echo "  - OPENAI_API_KEY"
	@echo "  - KAGGLE_USERNAME"
	@echo "  - KAGGLE_KEY"
	@echo "  - POSTGRES_PASSWORD"
	@echo ""
	@echo "Setup complete! Run 'make up' to start the services."

# Database operations
db-reset:
	docker-compose down -v
	docker-compose up -d postgres
	sleep 10
	docker-compose up -d

db-backup:
	docker-compose exec postgres pg_dump -U postgres ai_data_engineering > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	docker-compose exec -T postgres psql -U postgres ai_data_engineering < $(BACKUP_FILE)

# Monitoring
status:
	docker-compose ps

health:
	@echo "Checking service health..."
	@curl -f http://localhost:8501/_stcore/health || echo "App not healthy"
	@docker-compose exec postgres pg_isready -U postgres || echo "Database not healthy"

# Production
prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "See README.md for complete documentation"

# Linting and formatting
lint:
	flake8 src/
	mypy src/

format:
	black src/
	isort src/

# Security
security:
	@echo "Running security checks..."
	safety check
	bandit -r src/
