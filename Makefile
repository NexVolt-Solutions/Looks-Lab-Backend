.PHONY: help build up down restart logs shell db-shell test clean prod-build prod-up prod-down

help:
	@echo "Looks Lab - Docker Commands"
	@echo "============================"
	@echo "Development:"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View logs (ctrl+c to exit)"
	@echo "  make shell        - Open shell in app container"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Remove containers and volumes"
	@echo ""
	@echo "Production:"
	@echo "  make prod-build   - Build production images"
	@echo "  make prod-up      - Start production services"
	@echo "  make prod-down    - Stop production services"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo " Services started!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

shell:
	docker exec -it lookslab_app bash

db-shell:
	docker exec -it lookslab_db psql -U looks_lab -d looks_lab

test:
	docker-compose exec app pytest

clean:
	docker-compose down -v
	docker system prune -f

prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d
	@echo " Production services started!"

prod-down:
	docker-compose -f docker-compose.prod.yml down

