.PHONY: help dev build test lint format security-scan clean install setup docs deploy-dev deploy-staging deploy-prod

# Default target
help: ## Show this help message
	@echo "CloudOps Central - Development Commands"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Commands
dev: ## Start development environment
	@echo "Starting CloudOps Central development environment..."
	docker-compose up -d postgres redis
	@echo "Waiting for services to be ready..."
	@sleep 10
	cd src && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
	cd frontend && npm run dev &
	@echo "Development environment started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

dev-full: ## Start full development environment with monitoring
	@echo "Starting full development environment..."
	docker-compose up -d
	@echo "Full environment started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3001 (admin/admin123)"

stop: ## Stop all services
	docker-compose down
	@echo "All services stopped."

restart: ## Restart all services
	docker-compose down
	docker-compose up -d
	@echo "All services restarted."

# Setup Commands
setup: ## Initial project setup
	@echo "Setting up CloudOps Central..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from template"; fi
	@echo "Installing backend dependencies..."
	cd src && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Starting database..."
	docker-compose up -d postgres redis
	@sleep 10
	@echo "Running database migrations..."
	cd src && source venv/bin/activate && alembic upgrade head
	@echo "Setup complete!"

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd src && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Dependencies installed!"

# Database Commands
db-upgrade: ## Run database migrations
	cd src && alembic upgrade head

db-downgrade: ## Rollback database migration
	cd src && alembic downgrade -1

db-revision: ## Create new database migration
	@read -p "Enter migration message: " message; \
	cd src && alembic revision --autogenerate -m "$$message"

db-reset: ## Reset database (WARNING: destroys data)
	docker-compose down postgres
	docker volume rm cloudops-central_postgres_data
	docker-compose up -d postgres
	@sleep 10
	cd src && alembic upgrade head

# Testing Commands
test: ## Run all tests
	@echo "Running backend tests..."
	cd src && python -m pytest tests/ -v --cov=app --cov-report=html
	@echo "Running frontend tests..."
	cd frontend && npm test -- --coverage
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v

test-backend: ## Run backend tests only
	cd src && python -m pytest tests/ -v --cov=app --cov-report=html

test-frontend: ## Run frontend tests only
	cd frontend && npm test -- --coverage

test-e2e: ## Run end-to-end tests
	cd tests/e2e && npm run test

test-integration: ## Run integration tests
	python -m pytest tests/integration/ -v

test-performance: ## Run performance tests
	cd tests/performance && python -m pytest . -v

# Code Quality Commands
lint: ## Run linting for all code
	@echo "Linting backend code..."
	cd src && python -m black . --check
	cd src && python -m isort . --check-only
	cd src && python -m flake8 .
	cd src && python -m mypy .
	@echo "Linting frontend code..."
	cd frontend && npm run lint

format: ## Format all code
	@echo "Formatting backend code..."
	cd src && python -m black .
	cd src && python -m isort .
	@echo "Formatting frontend code..."
	cd frontend && npm run format

security-scan: ## Run security scans
	@echo "Running security scans..."
	cd src && python -m bandit -r app/
	cd src && python -m safety check
	cd frontend && npm audit
	@echo "Scanning for secrets..."
	git secrets --scan || echo "No secrets found"

# Build Commands
build: ## Build all containers
	docker-compose build

build-backend: ## Build backend container
	docker-compose build backend

build-frontend: ## Build frontend container
	docker-compose build frontend

# Infrastructure Commands
infra-plan: ## Plan Terraform infrastructure
	cd infrastructure && terraform plan

infra-apply: ## Apply Terraform infrastructure
	cd infrastructure && terraform apply

infra-destroy: ## Destroy Terraform infrastructure (WARNING)
	cd infrastructure && terraform destroy

infra-init: ## Initialize Terraform
	cd infrastructure && terraform init

# Documentation Commands
docs: ## Generate documentation
	@echo "Generating API documentation..."
	cd src && python -m app.utils.doc_generator
	@echo "Building user documentation..."
	cd docs && make html
	@echo "Documentation generated!"

docs-serve: ## Serve documentation locally
	cd docs/_build/html && python -m http.server 8080

# Monitoring Commands
logs: ## Show application logs
	docker-compose logs -f backend

logs-tail: ## Tail all logs
	docker-compose logs -f

metrics: ## Show metrics dashboard
	@echo "Metrics available at:"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3001"

# Deployment Commands
deploy-dev: ## Deploy to development environment
	@echo "Deploying to development..."
	kubectl apply -f deployments/overlays/dev/
	@echo "Development deployment complete!"

deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	kubectl apply -f deployments/overlays/staging/
	@echo "Staging deployment complete!"

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	@read -p "Are you sure you want to deploy to production? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		kubectl apply -f deployments/overlays/prod/; \
		echo "Production deployment complete!"; \
	else \
		echo "Production deployment cancelled."; \
	fi

# Backup Commands
backup: ## Create database backup
	@echo "Creating database backup..."
	@mkdir -p backups
	docker exec cloudops-postgres pg_dump -U cloudops cloudops_central > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/ directory"

restore: ## Restore database from backup
	@read -p "Enter backup file path: " backup_file; \
	docker exec -i cloudops-postgres psql -U cloudops cloudops_central < $$backup_file

# Utility Commands
clean: ## Clean up build artifacts and caches
	@echo "Cleaning up..."
	docker-compose down --volumes --remove-orphans
	docker system prune -f
	cd src && find . -type d -name "__pycache__" -exec rm -rf {} +
	cd src && find . -name "*.pyc" -delete
	cd frontend && rm -rf node_modules/.cache
	cd frontend && rm -rf build
	@echo "Cleanup complete!"

ps: ## Show running containers
	docker-compose ps

shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

shell-db: ## Open database shell
	docker-compose exec postgres psql -U cloudops cloudops_central

health: ## Check service health
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health || echo "Backend: DOWN"
	@curl -s http://localhost:3000 > /dev/null && echo "Frontend: UP" || echo "Frontend: DOWN"
	@docker-compose exec postgres pg_isready -U cloudops && echo "Database: UP" || echo "Database: DOWN"
	@docker-compose exec redis redis-cli ping && echo "Redis: UP" || echo "Redis: DOWN"

version: ## Show version information
	@echo "CloudOps Central v1.0.0"
	@echo "Python: $(shell python --version)"
	@echo "Node.js: $(shell node --version)"
	@echo "Docker: $(shell docker --version)"
	@echo "Terraform: $(shell terraform version | head -n1)"