# CloudOps Central CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment of CloudOps Central.

## Workflows Overview

### 1. CI - Tests and Quality Checks (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**Jobs:**

#### Lint Job
- Code formatting check with Black
- Import sorting with isort
- Code linting with Flake8
- Type checking with MyPy

#### Security Job
- Security scanning with Bandit
- Dependency vulnerability check with Safety

#### Unit Tests
- Runs all unit tests in `tests/unit/`
- PostgreSQL 15 and Redis 7 services
- Code coverage reporting
- Uploads coverage to Codecov
- Coverage artifacts retained for 7 days

#### Integration Tests
- Runs all integration tests in `tests/integration/`
- Full database and Redis services
- API endpoint testing
- Coverage reporting

#### E2E Tests
- Runs end-to-end workflow tests in `tests/e2e/`
- Complete user journey testing
- Coverage reporting

#### Test Summary
- Aggregates all test results
- Fails if any critical test fails
- Provides summary of all checks

**Required Secrets:**
- None (uses default `GITHUB_TOKEN`)

**Optional Secrets:**
- `CODECOV_TOKEN` - For Codecov integration (recommended)

---

### 2. Docker Build and Push (`docker-build-push.yml`)

**Triggers:**
- Push to `main` branch
- Version tags (`v*.*.*`)
- Release publications
- Manual workflow dispatch

**Jobs:**

#### Build and Test
Builds three Docker targets:
- `production` - Backend API server (Gunicorn + Uvicorn)
- `celery-worker` - Background task worker
- `celery-beat` - Task scheduler

**Features:**
- Multi-stage build caching
- Health check testing
- Push to GitHub Container Registry (GHCR)
- Image tagging strategy:
  - Branch name tags
  - SHA-based tags
  - Semantic version tags
  - Latest tags (on release)

#### Push Latest on Release
- Only runs when a release is published
- Pushes images with `latest` tag
- Pushes version-specific tags

#### Create Deployment Manifest
- Generates deployment manifest with version info
- Includes image digests and tags
- Provides deployment commands
- Retained for 90 days

#### Security Scan
- Scans images with Trivy
- Detects HIGH and CRITICAL vulnerabilities
- Uploads results to GitHub Security tab
- SARIF format reports

#### Build Summary
- Aggregates build results
- Reports success/failure status
- Provides image registry URLs

**Required Secrets:**
- None (uses default `GITHUB_TOKEN`)

**Permissions Required:**
- `contents: read` - Read repository contents
- `contents: write` - Create deployment manifests
- `packages: write` - Push to GHCR
- `security-events: write` - Upload security scans

---

## Image Registry

All images are pushed to GitHub Container Registry (GHCR):

```
ghcr.io/<username>/cloudops-central:latest-production
ghcr.io/<username>/cloudops-central:latest-celery-worker
ghcr.io/<username>/cloudops-central:latest-celery-beat
```

### Pulling Images

Images are public and can be pulled without authentication:

```bash
docker pull ghcr.io/<username>/cloudops-central:latest-production
```

For private repositories, authenticate with:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin
```

---

## Running Tests Locally

### All Tests
```bash
cd src
pytest tests/ -v --cov=app
```

### Unit Tests Only
```bash
cd src
pytest tests/unit/ -v
```

### Integration Tests Only
```bash
cd src
pytest tests/integration/ -v
```

### E2E Tests Only
```bash
cd src
pytest tests/e2e/ -v
```

### With Coverage Report
```bash
cd src
pytest tests/ -v --cov=app --cov-report=html
open htmlcov/index.html
```

### Run Specific Test Markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only e2e tests
pytest -m e2e

# Skip slow tests
pytest -m "not slow"
```

---

## Building Docker Images Locally

### Build Production Image
```bash
cd src
docker build --target production -t cloudops-central:local .
```

### Build All Targets
```bash
cd src
docker build --target production -t cloudops-central:backend .
docker build --target celery-worker -t cloudops-central:worker .
docker build --target celery-beat -t cloudops-central:beat .
```

### Test Image
```bash
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  cloudops-central:local
```

---

## Release Process

### Creating a Release

1. **Update Version**
   ```bash
   # Update version in:
   # - src/app/core/config.py (APP_VERSION)
   # - Update CHANGELOG.md
   ```

2. **Create Git Tag**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. **Create GitHub Release**
   - Go to GitHub Releases page
   - Click "Create a new release"
   - Select the tag
   - Add release notes
   - Publish release

4. **Automated Actions**
   - CI tests run automatically
   - Docker images built and pushed to GHCR
   - Images tagged with version and `latest`
   - Deployment manifest created
   - Security scans performed

### Version Tagging Strategy

- `v1.0.0` - Stable releases
- `v1.0.0-rc.1` - Release candidates
- `v1.0.0-beta.1` - Beta releases
- `v1.0.0-alpha.1` - Alpha releases

---

## Monitoring CI/CD

### View Workflow Runs
- Navigate to repository → Actions tab
- Select workflow from left sidebar
- View run history and logs

### Check Image Packages
- Navigate to repository → Packages
- View all published images
- See download statistics

### Security Alerts
- Navigate to repository → Security → Code scanning
- View Trivy scan results
- Review vulnerabilities

---

## Troubleshooting

### Tests Failing

1. **Check Service Connectivity**
   - Ensure PostgreSQL and Redis services are running
   - Verify connection strings in environment variables

2. **Check Dependencies**
   - Update `requirements.txt` if needed
   - Clear pip cache: `pip cache purge`

3. **Check Database Migrations**
   - Run migrations: `alembic upgrade head`
   - Reset test database if needed

### Docker Build Failing

1. **Check Dockerfile Syntax**
   - Validate Dockerfile: `docker build --check .`

2. **Clear Build Cache**
   ```bash
   docker builder prune -a
   ```

3. **Check Context Size**
   - Ensure `.dockerignore` is properly configured
   - Remove large unnecessary files

### GHCR Push Failing

1. **Check Permissions**
   - Verify `packages: write` permission in workflow
   - Ensure `GITHUB_TOKEN` has correct scope

2. **Check Image Size**
   - GHCR has size limits
   - Optimize image layers

---

## Best Practices

1. **Always run tests locally before pushing**
2. **Keep Docker images small** - Use multi-stage builds
3. **Tag semantically** - Follow SemVer
4. **Review security scans** - Address HIGH/CRITICAL issues
5. **Monitor CI/CD costs** - GitHub Actions minutes
6. **Keep dependencies updated** - Regular `pip update`
7. **Write tests for new features** - Maintain coverage >80%

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Pytest Documentation](https://docs.pytest.org/)
