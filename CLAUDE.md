# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

CloudOps Central is an enterprise-grade multi-cloud infrastructure management platform built with a microservices architecture. The system provides unified management of AWS, Azure, and GCP resources with features for cost optimization, policy enforcement, drift detection, and GitOps workflows.

## Architecture

### Microservices Design
The platform follows a service-oriented architecture with three primary domains:
- **Infrastructure Service**: Multi-cloud resource discovery, drift detection, and automated remediation
- **Cost Service**: Real-time cost tracking, anomaly detection, and AI-driven optimization recommendations
- **Policy Service**: Compliance rules engine, security scanning, and policy-as-code enforcement

### Data Flow
```
Client Request → API Gateway (FastAPI) → Service Layer → Database/Cache
                      ↓
                Middleware Stack:
                - Authentication (OAuth2/JWT)
                - Rate Limiting
                - Security Headers
                - Logging & Monitoring
```

### Database Architecture
- **PostgreSQL**: Primary data store with async SQLAlchemy ORM
- **Redis**: Caching (DB 0), Celery broker (DB 1), and result backend (DB 2)
- All models inherit from `BaseModel` which provides: UUID primary keys, timestamps, soft deletes, metadata/tags support, and audit tracking

### Async Patterns
The entire backend uses async/await with SQLAlchemy's async engine. All database operations use `AsyncSession` and the dependency injection pattern with `get_db()`.

## Development Commands

### Initial Setup
```bash
# Create .env from template and configure
cp .env.example .env

# Run full setup (creates venv, installs deps, runs migrations)
make setup

# Or manual setup:
cd src && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d postgres redis
alembic upgrade head
```

### Running the Application
```bash
# Start minimal dev environment (backend + postgres + redis)
make dev

# Start full environment with monitoring (includes Prometheus/Grafana)
make dev-full

# Backend only (manual)
cd src && source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend only
cd frontend && npm run dev
```

### Testing
```bash
# Run all tests (backend + frontend + integration)
make test

# Backend tests with coverage
make test-backend
# or: cd src && pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
make test-frontend
# or: cd frontend && npm test -- --coverage

# End-to-end tests
make test-e2e

# Performance tests
make test-performance

# Run single test file
cd src && pytest tests/path/to/test_file.py -v

# Run single test function
cd src && pytest tests/path/to/test_file.py::test_function_name -v
```

### Database Operations
```bash
# Run migrations
make db-upgrade
# or: cd src && alembic upgrade head

# Rollback one migration
make db-downgrade
# or: cd src && alembic downgrade -1

# Create new migration
make db-revision
# or: cd src && alembic revision --autogenerate -m "description"

# Database shell access
make shell-db
# or: docker-compose exec postgres psql -U cloudops cloudops_central

# Reset database (WARNING: destroys all data)
make db-reset
```

### Code Quality
```bash
# Lint all code (black, isort, flake8, mypy, eslint)
make lint

# Format all code
make format

# Security scanning (bandit, safety, npm audit)
make security-scan
```

### Infrastructure & Deployment
```bash
# Terraform operations
make infra-init    # Initialize Terraform
make infra-plan    # Plan infrastructure changes
make infra-apply   # Apply infrastructure changes

# Deploy to environments
make deploy-dev
make deploy-staging
make deploy-prod   # Requires confirmation
```

### Monitoring & Debugging
```bash
# View application logs
make logs          # Backend logs
make logs-tail     # All service logs

# Health checks
make health

# Access monitoring dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin123)
# API Docs: http://localhost:8000/api/v1/docs
```

## Key Implementation Details

### Configuration Management
Settings are managed via `app/core/config.py` using Pydantic Settings:
- All settings loaded from environment variables or `.env` file
- Access via `get_settings()` which provides caching via `@lru_cache`
- Database URL automatically constructed from individual components if needed
- Environment validation ensures only valid values (development/staging/production/testing)

### Database Models
All models should inherit from appropriate base classes in `app/models/base.py`:
- `BaseModel`: Includes UUID, timestamps, soft delete, metadata, and audit fields
- `NamedModel`: Adds name, description, and status fields
- Available mixins: `TimestampMixin`, `UUIDMixin`, `SoftDeleteMixin`, `MetadataMixin`, `AuditMixin`, `StatusMixin`

### Service Layer Pattern
Business logic lives in service classes (not in API routes):
- Services receive `AsyncSession` via dependency injection
- API routes in `app/api/v1/` should be thin, delegating to services
- Services in `app/services/` contain all business logic
- All services use async methods with proper error handling

### Middleware Stack
Applied in order (see `main.py`):
1. `TrustedHostMiddleware` - Host validation
2. `CORSMiddleware` - Cross-origin requests
3. `SessionMiddleware` - Session management
4. `SecurityHeadersMiddleware` - Security headers
5. `LoggingMiddleware` - Request/response logging
6. `RateLimitMiddleware` - Rate limiting (100/min default)
7. `AuthenticationMiddleware` - OAuth2/JWT validation

### Error Handling
- Custom exceptions inherit from `CloudOpsException` in `app/core/exceptions.py`
- Global exception handlers in `main.py` provide consistent error responses
- All errors include: type, message, details, timestamp, request_id

### Background Tasks
Celery is configured with Redis broker for async task execution:
- Broker: Redis DB 1 (`redis://localhost:6379/1`)
- Result Backend: Redis DB 2 (`redis://localhost:6379/2`)
- Workers: `celery -A app.core.celery worker --loglevel=info`
- Scheduler: `celery -A app.core.celery beat --loglevel=info`

### Multi-Cloud Integration
Cloud provider SDKs are available:
- **AWS**: boto3 (primary cloud provider)
- **Azure**: azure-identity, azure-mgmt-resource, azure-mgmt-compute
- **GCP**: google-cloud-compute, google-cloud-storage
- Credentials configured via environment variables

### Docker Compose Services
The `docker-compose.yml` defines:
- `postgres`: PostgreSQL 15 on port 5432
- `redis`: Redis 7 on port 6379
- `backend`: FastAPI app on port 8000
- `celery-worker`: Background task worker
- `celery-beat`: Scheduled task scheduler
- `frontend`: React app on port 3000 (if implemented)
- `prometheus`: Metrics on port 9090
- `grafana`: Dashboards on port 3001
- `nginx`: Reverse proxy on ports 80/443

### API Structure
All API routes are versioned under `/api/v1`:
- `/api/v1/infrastructure` - Multi-cloud resource management
- `/api/v1/costs` - Cost tracking and optimization
- `/api/v1/policies` - Policy engine and compliance
- `/api/v1/users` - User management
- `/health` - Health check endpoint
- `/api/v1/docs` - OpenAPI documentation

### Authentication Flow
OAuth2 with JWT tokens:
- Access tokens expire in 60 minutes (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh tokens expire in 30 days (configurable via `JWT_REFRESH_TOKEN_EXPIRE_DAYS`)
- JWT secret configurable via `JWT_SECRET_KEY` environment variable
- Passwords hashed with bcrypt (12 rounds default)

## Common Patterns

### Creating a New API Endpoint
1. Define request/response models using Pydantic
2. Add business logic method to appropriate service in `app/services/`
3. Create route in `app/api/v1/[domain].py`
4. Include router in `app/api/router.py` if new domain
5. Add tests in `tests/`

### Adding a Database Model
1. Create model class inheriting from `BaseModel` or `NamedModel` in `app/models/`
2. Import in `app/models/__init__.py`
3. Create migration: `cd src && alembic revision --autogenerate -m "Add model_name"`
4. Review and edit migration in `src/alembic/versions/`
5. Apply migration: `alembic upgrade head`

### Working with Async Database
```python
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def my_endpoint(db: AsyncSession = Depends(get_db)):
    # Query example
    result = await db.execute(select(Model).where(...))
    items = result.scalars().all()

    # Create example
    new_item = Model(...)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
```

### Adding Background Tasks
1. Define task in appropriate service module
2. Decorate with `@celery_app.task`
3. Call with `.delay()` or `.apply_async()`
4. Monitor via Celery logs or Flower (if configured)

## Important Notes

- **Database Connections**: Always use async patterns with `AsyncSession`. The connection pool is configured with 10 base connections and 20 overflow.
- **Alembic Migrations**: Currently, no `alembic.ini` or migrations exist. You'll need to create these when implementing the database layer fully.
- **Frontend**: The frontend is listed in architecture but not yet implemented in the repository.
- **Feature Flags**: All major features (cost optimization, policy engine, drift detection, backup automation) are enabled by default and can be toggled via environment variables.
- **Testing**: Testing infrastructure is defined but actual test files need to be created.
- **Terraform**: Infrastructure code referenced but not yet present in repository.

## Testing

### Test Structure
```
src/tests/
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests for individual components
│   ├── test_database.py
│   ├── test_models.py
│   ├── test_exceptions.py
│   ├── test_config.py
│   └── test_services.py
├── integration/          # API integration tests
│   ├── test_infrastructure_api.py
│   ├── test_costs_api.py
│   └── test_policies_api.py
└── e2e/                  # End-to-end workflow tests
    └── test_infrastructure_workflow.py
```

### Running Tests

```bash
# All tests with coverage
cd src && pytest tests/ -v --cov=app --cov-report=html

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v

# Run specific test file
pytest tests/unit/test_models.py -v

# Run specific test function
pytest tests/unit/test_models.py::TestCloudProviderModel::test_create_cloud_provider -v

# Run tests with markers
pytest -m unit           # Only unit tests
pytest -m integration    # Only integration tests
pytest -m "not slow"     # Skip slow tests
```

### Test Configuration
- Configuration in `pytest.ini`
- Fixtures in `conftest.py` including database, HTTP clients, and mock services
- Minimum coverage threshold: 80%
- Async tests use `pytest-asyncio`

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.database` - Requires database
- `@pytest.mark.redis` - Requires Redis

## CI/CD Pipeline

### GitHub Actions Workflows

#### CI Workflow (`ci.yml`)
Runs on every push and pull request to `main` or `develop`:

1. **Lint Job**: Black, isort, Flake8, MyPy
2. **Security Job**: Bandit, Safety
3. **Unit Tests**: With PostgreSQL and Redis services
4. **Integration Tests**: Full API testing
5. **E2E Tests**: Complete workflow testing
6. **Test Summary**: Aggregates all results

All tests run in parallel with dedicated PostgreSQL 15 and Redis 7 service containers.

#### Docker Build & Push Workflow (`docker-build-push.yml`)
Runs on push to `main`, version tags, and releases:

1. **Build and Test**: Builds three targets (production, celery-worker, celery-beat)
2. **Push to GHCR**: Pushes images to GitHub Container Registry
3. **Security Scan**: Trivy vulnerability scanning
4. **Create Manifest**: Generates deployment manifest on releases

### Docker Images

All images are pushed to GHCR with semantic versioning:

```bash
# Pull images
docker pull ghcr.io/<username>/cloudops-central:latest-production
docker pull ghcr.io/<username>/cloudops-central:latest-celery-worker
docker pull ghcr.io/<username>/cloudops-central:latest-celery-beat

# Version-specific tags
docker pull ghcr.io/<username>/cloudops-central:v1.0.0-production
```

### Release Process

1. Update version in `app/core/config.py`
2. Create and push git tag: `git tag -a v1.0.0 -m "Release 1.0.0" && git push origin v1.0.0`
3. Create GitHub release from the tag
4. CI/CD automatically builds, tests, and pushes Docker images
5. Images tagged with version number and `latest`

### Building Docker Images Locally

```bash
# Build production image
cd src && docker build --target production -t cloudops-central:local .

# Build celery worker
cd src && docker build --target celery-worker -t cloudops-central:worker .

# Build celery beat
cd src && docker build --target celery-beat -t cloudops-central:beat .
```

### Dependabot Configuration

Automated dependency updates are configured via `.github/dependabot.yml`:

- **Python Dependencies**: Weekly updates every Monday at 09:00 UTC
  - Grouped updates for dev, testing, and linting dependencies
  - Automatic assignment to @georg-nikola
  - Labeled with `dependencies` and `python`

- **GitHub Actions**: Weekly updates for workflow actions
  - Labeled with `dependencies` and `github-actions`

- **Docker**: Weekly updates for base images in Dockerfiles
  - Labeled with `dependencies` and `docker`

**Pull Request Limits**:
- Python: 10 open PRs maximum
- GitHub Actions: 5 open PRs maximum
- Docker: 5 open PRs maximum

**Versioning Strategy**: `increase` - Always update to the latest allowed version

### Qodo (Codium AI) Code Review

AI-powered code review is configured via `.github/workflows/qodo.yml` and `.github/qodo-config.toml`.

**Required Setup**:
Add `OPENAI_API_KEY` to GitHub repository secrets:
```bash
gh secret set OPENAI_API_KEY --body "sk-..."
```

**Features**:
- **PR Review**: Automatic code review on every PR (opened, synchronized, reopened)
- **Code Improvements**: AI-generated suggestions for enhancements
- **PR Description**: Auto-generated PR descriptions with CloudOps-specific focus
- **Security Review**: Security implications highlighted
- **Test Recommendations**: Suggests tests for new code
- **Cost Optimization**: Notes cost optimization opportunities

**Configuration Highlights** (`.github/qodo-config.toml`):
- Model: GPT-4 with GPT-3.5-turbo fallback
- 4 code suggestions per review
- Inline code comments enabled
- Focus areas: Infrastructure, cloud operations, security, compliance, cost optimization

**Workflow Jobs**:
1. `qodo-review`: Comprehensive code review
2. `qodo-improve`: Improvement suggestions
3. `qodo-describe`: PR description generation (on PR open only)

### Branch Protection Rules

The `main` branch is protected with the following rules:

**Required Status Checks** (must pass before merge):
- Code Quality Checks
- Security Scanning
- Unit Tests
- Integration Tests
- End-to-End Tests

**Pull Request Requirements**:
- At least 1 approving review required
- Stale reviews automatically dismissed when new commits are pushed
- All conversations must be resolved before merge

**Branch Restrictions**:
- Force pushes blocked
- Branch deletions blocked
- Admins also subject to these restrictions

**Fork-Based Workflow**:
All code changes should be submitted via pull requests from forks. This ensures:
- Clean separation between upstream and contributor changes
- Better security through reduced direct push access
- Standard review process for all changes

To contribute:
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/cloudops-central.git
cd cloudops-central

# Add upstream remote
git remote add upstream https://github.com/georg-nikola/cloudops-central.git

# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add . && git commit -m "feat: my feature"

# Push to your fork
git push origin feature/my-feature

# Create PR from your fork to upstream main
gh pr create --web
```

**Note**: The branch protection configuration is stored in `.github/branch-protection.json` and can be updated via:
```bash
gh api repos/{owner}/{repo}/branches/main/protection --method PUT --input .github/branch-protection.json
```

## Environment Configuration

Critical environment variables (from `.env.example`):
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret key (change in production!)
- `JWT_SECRET_KEY`: JWT signing key (change in production!)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `ENVIRONMENT`: One of: development, staging, production, testing
- `DEBUG`: Boolean, should be false in production
