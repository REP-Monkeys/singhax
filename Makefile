# ConvoTravelInsure Development Makefile

.PHONY: help up down logs migrate seed test clean install

# Default target
help:
	@echo "ConvoTravelInsure Development Commands:"
	@echo ""
	@echo "  make up          - Start all services (db, backend, frontend)"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make migrate     - Run database migrations"
	@echo "  make seed        - Load seed data"
	@echo "  make test        - Run tests (backend and frontend)"
	@echo "  make clean       - Clean up containers and volumes"
	@echo "  make install     - Install dependencies for all services"
	@echo ""

# Start all services
up:
	@echo "Starting ConvoTravelInsure services..."
	docker-compose up -d
	@echo "Services started! Frontend: http://localhost:3000, Backend: http://localhost:8000"

# Stop all services
down:
	@echo "Stopping ConvoTravelInsure services..."
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Run database migrations
migrate:
	@echo "Running database migrations..."
	docker-compose exec backend alembic upgrade head

# Load seed data
seed:
	@echo "Loading seed data..."
	docker-compose exec backend python -m app.scripts.seed_data

# Run tests
test:
	@echo "Running backend tests..."
	docker-compose exec backend pytest
	@echo "Running frontend tests..."
	docker-compose exec frontend npm test

# Clean up
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	docker system prune -f

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd apps/backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd apps/frontend && npm install

# Development shortcuts
dev: up
	@echo "Development environment ready!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

# Database operations
db-shell:
	docker-compose exec db psql -U postgres -d convo_travel_insure

# Backend operations
backend-shell:
	docker-compose exec backend bash

# Frontend operations
frontend-shell:
	docker-compose exec frontend sh

# Quick restart
restart: down up
	@echo "Services restarted!"

# Production build
build:
	@echo "Building production images..."
	docker-compose build

# Production deploy
deploy: build
	@echo "Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d
