.PHONY: help build up down restart logs logs-backend logs-db ps clean test test-fast test-unit fresh-start dev-up dev-down db-start db-stop db-restart db-logs db-clean

# Default target - show help
.DEFAULT_GOAL := help

help:
	@echo "DF HealthBench - Available Commands:"
	@echo ""
	@echo "Production Commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services (detached)"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs (all services)"
	@echo "  make logs-backend   - View backend logs only"
	@echo "  make logs-db        - View database logs only"
	@echo "  make ps             - Show service status"
	@echo "  make clean          - Stop services and remove volumes (⚠️  destroys data)"
	@echo "  make fresh-start    - Complete reset: down + rebuild + start (⚠️  destroys data)"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev-up         - Start development environment with hot-reload"
	@echo "  make dev-down       - Stop development environment"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test           - Run full pytest test suite (~10-15 min)"
	@echo "  make test-fast      - Run fast tests only (skip slow LLM calls)"
	@echo "  make test-unit      - Run unit tests only (no DB/API required)"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-start       - Start database only"
	@echo "  make db-stop        - Stop database"
	@echo "  make db-restart     - Restart database"
	@echo "  make db-logs        - View database logs"
	@echo "  make db-clean       - Remove database volumes (⚠️  destroys data)"

# Docker Compose Commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-db:
	docker-compose logs -f postgres

ps:
	docker-compose ps

clean:
	@echo "⚠️  WARNING: This will destroy all data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	docker-compose down -v

fresh-start:
	@echo "🔄 Complete reset: down + rebuild + start"
	@echo "⚠️  WARNING: This will destroy all application data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	@echo "📦 Stopping all services and removing volumes..."
	docker-compose down -v
	@echo "🔨 Rebuilding images..."
	docker-compose build
	@echo "🚀 Starting services..."
	docker-compose up -d
	@echo "✅ Fresh start complete! Check logs: make logs"

# Development Environment (with hot-reload)
dev-up:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

dev-down:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Testing Commands
test:
	@echo "🧪 Running full pytest test suite..."
	cd backend && poetry run pytest -v

test-fast:
	@echo "⚡ Running fast tests only (skipping slow LLM calls)..."
	cd backend && poetry run pytest -m "not slow" -v

test-unit:
	@echo "🎯 Running unit tests only (no DB/API required)..."
	cd backend && poetry run pytest -m unit -v

# Database Commands (kept for backwards compatibility)
db-start:
	docker-compose up -d postgres

db-stop:
	docker-compose down

db-restart:
	docker-compose restart postgres

db-logs:
	docker-compose logs -f postgres

db-clean:
	@echo "⚠️  WARNING: This will destroy all database data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	docker-compose down -v

