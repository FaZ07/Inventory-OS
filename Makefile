.PHONY: help up down build logs shell-backend shell-db migrate seed test lint format

help:
	@echo "InventoryOS — Available commands:"
	@echo "  make up          Start all services"
	@echo "  make down        Stop all services"
	@echo "  make build       Rebuild images"
	@echo "  make logs        Tail logs"
	@echo "  make migrate     Run DB migrations"
	@echo "  make seed        Seed demo data"
	@echo "  make test        Run test suite"
	@echo "  make lint        Run linters"
	@echo "  make format      Format code"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f backend

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U inventoryos -d inventoryos

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.scripts.seed

test:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=html

lint:
	docker compose exec backend ruff check app/
	cd frontend && npx eslint src/

format:
	docker compose exec backend ruff format app/
	cd frontend && npx prettier --write src/

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev
