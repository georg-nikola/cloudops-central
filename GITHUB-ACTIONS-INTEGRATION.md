# GitHub Actions Integration Guide

This guide explains how to integrate the DevMind Pipeline ML services with your GitHub Actions workflows to enable AI-powered build optimization, failure prediction, and intelligent test selection.

## Table of Contents

1. [Overview](#overview)
2. [Service Endpoints](#service-endpoints)
3. [Integration Patterns](#integration-patterns)
4. [Example Workflows](#example-workflows)
5. [Authentication](#authentication)
6. [Best Practices](#best-practices)

## Overview

DevMind Pipeline provides three ML-powered services accessible via REST API:

- **Build Optimizer**: Predicts build time and suggests optimizations
- **Failure Predictor**: Predicts likelihood of pipeline failure
- **Test Intelligence**: Intelligently selects which tests to run

### Service Location

**Production**:
```
https://devmind.example.com
```

**Local Development**:
```
http://localhost:8000
```

**Kubernetes Cluster**:
```
http://devmind-pipeline.devmind-pipeline.svc.cluster.local:8000
```

## Service Endpoints

### Build Optimizer

**Predict Build Time**:
```bash
POST /api/v1/build-optimizer/predict
Content-Type: application/json

{
  "dependency_count": 45,
  "code_change_size": 1200,
  "file_count": 23,
  "test_count": 156,
  "historical_build_time": 420,
  "branch_complexity": 3,
  "commit_frequency": 12,
  "package_size": 5600
}
```

**Response**:
```json
{
  "predicted_build_time_seconds": 385,
  "confidence": 0.92,
  "optimization_suggestions": [
    "Parallelize test execution",
    "Cache dependencies",
    "Use incremental builds"
  ]
}
```

### Failure Predictor

**Predict Pipeline Failure**:
```bash
POST /api/v1/failure-predictor/predict
Content-Type: application/json

{
  "pipeline_duration_mean": 450,
  "pipeline_duration_std": 120,
  "failure_rate_7d": 0.05,
  "code_churn": 2300,
  "test_coverage": 0.78,
  "deployment_frequency": 12,
  "error_rate": 0.02,
  "response_time_p95": 850,
  "resource_utilization": 0.65
}
```

**Response**:
```json
{
  "failure_probability": 0.18,
  "risk_level": "LOW",
  "risk_factors": [
    "Above average pipeline duration",
    "Recent code changes"
  ],
  "recommendations": [
    "Run additional integration tests",
    "Review recent changes"
  ]
}
```

### Test Intelligence

**Select Tests to Run**:
```bash
POST /api/v1/test-intelligence/select
Content-Type: application/json

{
  "changed_files": [
    "src/core/config.py",
    "src/services/ml_service_manager.py"
  ],
  "all_tests": [
    "tests/test_config.py",
    "tests/test_main.py",
    "tests/test_services.py",
    "tests/integration/test_api.py"
  ]
}
```

**Response**:
```json
{
  "selected_tests": [
    "tests/test_config.py",
    "tests/test_services.py"
  ],
  "skipped_tests": [
    "tests/test_main.py",
    "tests/integration/test_api.py"
  ],
  "estimated_time_saved": 240,
  "confidence": 0.85
}
```

### Health Check

**Check Service Status**:
```bash
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "models": {
    "build_optimizer": "ready",
    "failure_predictor": "ready",
    "test_intelligence": "ready"
  }
}
```

## Integration Patterns

### Pattern 1: Intelligent Test Selection

Automatically select which tests to run based on code changes, reducing CI/CD time.

```yaml
name: Intelligent Test Selection

on: [push, pull_request]

env:
  DEVMIND_API: https://devmind.example.com

jobs:
  select-tests:
    runs-on: ubuntu-latest
    outputs:
      tests: ${{ steps.select.outputs.tests }}
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Get changed files
        id: files
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            FILES=$(git diff --name-only ${{ github.event.pull_request.base.sha }})
          else
            FILES=$(git diff --name-only HEAD~1)
          fi
          echo "changed_files=$(echo $FILES | tr '\n' ',')" >> $GITHUB_OUTPUT

      - name: Select tests with DevMind
        id: select
        run: |
          RESPONSE=$(curl -s -X POST "$DEVMIND_API/api/v1/test-intelligence/select" \
            -H "Content-Type: application/json" \
            -d '{
              "changed_files": ["'"$(echo '${{ steps.files.outputs.changed_files }}' | sed "s/,/\",\"/g")"'"],
              "all_tests": ["tests/test_config.py", "tests/test_main.py", "tests/integration/test_api.py"]
            }')

          TESTS=$(echo $RESPONSE | jq -r '.selected_tests | join(" ")')
          SAVED=$(echo $RESPONSE | jq -r '.estimated_time_saved')

          echo "tests=$TESTS" >> $GITHUB_OUTPUT
          echo "time_saved=$SAVED" >> $GITHUB_OUTPUT
          echo "Time saved by intelligent selection: ${SAVED}s"

  run-tests:
    needs: select-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r src/requirements.txt

      - name: Run selected tests
        run: |
          pytest ${{ needs.select-tests.outputs.tests }} -v
```

### Pattern 2: Failure Prediction and Risk Assessment

Assess pipeline risk and take preventive actions before failures occur.

```yaml
name: Failure Prediction

on: [push, pull_request]

env:
  DEVMIND_API: https://devmind.example.com

jobs:
  assess-risk:
    runs-on: ubuntu-latest
    outputs:
      risk_level: ${{ steps.assess.outputs.risk_level }}
      should_run_full_tests: ${{ steps.assess.outputs.should_run_full_tests }}
    steps:
      - uses: actions/checkout@v3

      - name: Collect metrics
        id: metrics
        run: |
          # Simulate metric collection (replace with real metrics)
          cat > metrics.json << 'EOF'
          {
            "pipeline_duration_mean": 450,
            "pipeline_duration_std": 120,
            "failure_rate_7d": 0.05,
            "code_churn": 2300,
            "test_coverage": 0.78,
            "deployment_frequency": 12,
            "error_rate": 0.02,
            "response_time_p95": 850,
            "resource_utilization": 0.65
          }
          EOF
          cat metrics.json

      - name: Predict failure risk
        id: assess
        run: |
          RESPONSE=$(curl -s -X POST "$DEVMIND_API/api/v1/failure-predictor/predict" \
            -H "Content-Type: application/json" \
            -d @metrics.json)

          RISK=$(echo $RESPONSE | jq -r '.risk_level')
          PROBABILITY=$(echo $RESPONSE | jq -r '.failure_probability')

          # Run full tests if risk is HIGH or MEDIUM
          if [ "$RISK" = "HIGH" ] || [ "$RISK" = "MEDIUM" ]; then
            FULL_TESTS="true"
          else
            FULL_TESTS="false"
          fi

          echo "risk_level=$RISK" >> $GITHUB_OUTPUT
          echo "should_run_full_tests=$FULL_TESTS" >> $GITHUB_OUTPUT
          echo "Failure probability: ${PROBABILITY}, Risk Level: ${RISK}"

  full-test-suite:
    needs: assess-risk
    if: needs.assess-risk.outputs.should_run_full_tests == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r src/requirements.txt

      - name: Run full test suite
        run: pytest tests/ -v --cov=src

  fast-test-suite:
    needs: assess-risk
    if: needs.assess-risk.outputs.should_run_full_tests == 'false'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r src/requirements.txt

      - name: Run quick tests
        run: pytest tests/test_config.py tests/test_main.py -v
```

### Pattern 3: Build Time Optimization

Optimize build strategy based on predicted build times.

```yaml
name: Build Optimization

on: [push, pull_request]

env:
  DEVMIND_API: https://devmind.example.com

jobs:
  plan-build:
    runs-on: ubuntu-latest
    outputs:
      parallelism: ${{ steps.plan.outputs.parallelism }}
      cache_strategy: ${{ steps.plan.outputs.cache_strategy }}
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Analyze code changes
        id: analyze
        run: |
          # Count metrics about the change
          DEPS=$(find . -name "requirements.txt" | wc -l)
          FILES=$(git diff --name-only HEAD~1 | wc -l)
          SIZE=$(git diff --stat HEAD~1 | tail -1 | awk '{print $4}')

          echo "dependency_count=$DEPS" >> $GITHUB_OUTPUT
          echo "file_count=$FILES" >> $GITHUB_OUTPUT
          echo "code_change_size=$SIZE" >> $GITHUB_OUTPUT

      - name: Predict build time and get recommendations
        id: plan
        run: |
          RESPONSE=$(curl -s -X POST "$DEVMIND_API/api/v1/build-optimizer/predict" \
            -H "Content-Type: application/json" \
            -d '{
              "dependency_count": ${{ steps.analyze.outputs.dependency_count }},
              "code_change_size": ${{ steps.analyze.outputs.code_change_size }},
              "file_count": ${{ steps.analyze.outputs.file_count }},
              "test_count": 150,
              "historical_build_time": 420,
              "branch_complexity": 3,
              "commit_frequency": 12,
              "package_size": 5600
            }')

          PREDICTED=$(echo $RESPONSE | jq -r '.predicted_build_time_seconds')

          # Set parallelism based on predicted time
          if [ $PREDICTED -gt 600 ]; then
            PARALLELISM=4
          elif [ $PREDICTED -gt 300 ]; then
            PARALLELISM=2
          else
            PARALLELISM=1
          fi

          echo "parallelism=$PARALLELISM" >> $GITHUB_OUTPUT
          echo "cache_strategy=aggressive" >> $GITHUB_OUTPUT
          echo "Predicted build time: ${PREDICTED}s, Parallelism: ${PARALLELISM}"

  build:
    needs: plan-build
    runs-on: ubuntu-latest
    strategy:
      matrix:
        job: [1, 2]
      max-parallel: ${{ needs.plan-build.outputs.parallelism }}
    steps:
      - uses: actions/checkout@v3

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Build
        run: |
          pip install -r src/requirements.txt
          python -m pytest src/tests/ -v
```

## Example Workflows

### Standalone DevMind Health Check

```yaml
name: DevMind Health Check

on:
  schedule:
    - cron: '0 * * * *'  # Hourly
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Check DevMind service health
        run: |
          RESPONSE=$(curl -s -X GET "https://devmind.example.com/health")
          STATUS=$(echo $RESPONSE | jq -r '.status')

          if [ "$STATUS" != "healthy" ]; then
            echo "⚠️ DevMind service is not healthy!"
            echo $RESPONSE | jq .
            exit 1
          fi

          echo "✅ DevMind service is healthy"
          echo $RESPONSE | jq .

      - name: Check model status
        run: |
          RESPONSE=$(curl -s -X GET "https://devmind.example.com/models/status")
          echo $RESPONSE | jq .
```

### Pull Request Analysis

```yaml
name: PR Analysis with DevMind

on: [pull_request]

env:
  DEVMIND_API: https://devmind.example.com

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Get PR metrics
        id: metrics
        run: |
          BASE_SHA=${{ github.event.pull_request.base.sha }}
          HEAD_SHA=${{ github.event.pull_request.head.sha }}

          # Calculate changes
          CHANGED_FILES=$(git diff --name-only $BASE_SHA...$HEAD_SHA)
          ADDITIONS=$(git diff --shortstat $BASE_SHA...$HEAD_SHA | awk '{print $4}' | cut -d'+' -f1)
          DELETIONS=$(git diff --shortstat $BASE_SHA...$HEAD_SHA | awk '{print $6}')

          echo "changed_files=$CHANGED_FILES" >> $GITHUB_OUTPUT
          echo "additions=$ADDITIONS" >> $GITHUB_OUTPUT
          echo "deletions=$DELETIONS" >> $GITHUB_OUTPUT

      - name: Get DevMind recommendations
        id: devmind
        run: |
          # Select tests
          RESPONSE=$(curl -s -X POST "$DEVMIND_API/api/v1/test-intelligence/select" \
            -H "Content-Type: application/json" \
            -d '{
              "changed_files": ["'"$(echo '${{ steps.metrics.outputs.changed_files }}' | sed "s/\n/\",\"/g")"'"],
              "all_tests": ["tests/test_config.py", "tests/test_main.py", "tests/integration/test_api.py"]
            }')

          TESTS=$(echo $RESPONSE | jq -r '.selected_tests | join(", ")')
          CONFIDENCE=$(echo $RESPONSE | jq -r '.confidence')

          echo "selected_tests=$TESTS" >> $GITHUB_OUTPUT
          echo "confidence=$CONFIDENCE" >> $GITHUB_OUTPUT

      - name: Comment on PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🤖 DevMind Analysis\n\n**Recommended Tests**: ${{ steps.devmind.outputs.selected_tests }}\n**Confidence**: ${{ steps.devmind.outputs.confidence }}\n\n**Changes**:\n- Files changed: ${{ steps.metrics.outputs.file_count }}\n- Additions: +${{ steps.metrics.outputs.additions }}\n- Deletions: -${{ steps.metrics.outputs.deletions }}`
            })
```

## Authentication

### API Key Authentication (if configured)

For production deployments with authentication:

```yaml
- name: Call DevMind API with authentication
  env:
    DEVMIND_API_KEY: ${{ secrets.DEVMIND_API_KEY }}
  run: |
    curl -X POST "https://devmind.example.com/api/v1/test-intelligence/select" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $DEVMIND_API_KEY" \
      -d '{...}'
```

**Setup in GitHub**:

1. Go to repository Settings → Secrets and variables → Actions
2. Create secret: `DEVMIND_API_KEY`
3. Use in workflow: `${{ secrets.DEVMIND_API_KEY }}`

### Token-based Authentication

```yaml
env:
  DEVMIND_TOKEN: ${{ secrets.DEVMIND_TOKEN }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Use DevMind token
        run: |
          curl -X POST "$DEVMIND_API/api/v1/build-optimizer/predict" \
            -H "Authorization: Token $DEVMIND_TOKEN" \
            -d '{...}'
```

## Best Practices

### 1. Cache API Responses

```yaml
- name: Cache DevMind predictions
  id: cache
  uses: actions/cache@v3
  with:
    path: .devmind-cache
    key: devmind-${{ github.event.pull_request.base.sha }}

- name: Use cached or fetch new predictions
  run: |
    if [ -f .devmind-cache/predictions.json ]; then
      echo "Using cached predictions"
      cat .devmind-cache/predictions.json
    else
      echo "Fetching fresh predictions from DevMind"
      # Call API and save to cache
    fi
```

### 2. Handle API Timeouts

```yaml
- name: Call DevMind with timeout
  run: |
    timeout 30s curl -s -X POST "$DEVMIND_API/api/v1/test-intelligence/select" \
      -H "Content-Type: application/json" \
      -d @payload.json || {
        echo "⚠️ DevMind API timeout, using fallback strategy"
        echo "tests=tests/" >> $GITHUB_OUTPUT
      }
```

### 3. Validate Service Health

```yaml
- name: Verify DevMind availability
  run: |
    MAX_RETRIES=3
    for i in $(seq 1 $MAX_RETRIES); do
      RESPONSE=$(curl -s -X GET "$DEVMIND_API/health")
      STATUS=$(echo $RESPONSE | jq -r '.status')

      if [ "$STATUS" = "healthy" ]; then
        echo "✅ DevMind is available"
        exit 0
      fi

      if [ $i -lt $MAX_RETRIES ]; then
        echo "Retry $i/$MAX_RETRIES..."
        sleep 5
      fi
    done

    echo "❌ DevMind unavailable, skipping optimization"
    exit 0  # Don't fail the workflow
```

### 4. Log DevMind Decisions

```yaml
- name: Document DevMind decisions
  run: |
    cat > .devmind-report.json << 'EOF'
    {
      "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
      "pr": ${{ github.event.pull_request.number }},
      "changed_files": ["..."],
      "selected_tests": ["..."],
      "confidence": 0.85,
      "predicted_time": 420
    }
    EOF

    # Upload as artifact for review
    echo "DevMind decisions logged to .devmind-report.json"
```

### 5. Environment Configuration

Create `.github/env/devmind.env`:

```bash
# DevMind API Configuration
DEVMIND_API=https://devmind.example.com
DEVMIND_TIMEOUT=30
DEVMIND_RETRIES=3
DEVMIND_SKIP_ON_FAILURE=true
```

Use in workflow:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DEVMIND_API: ${{ vars.DEVMIND_API }}
    steps:
      - run: echo "Using DevMind at $DEVMIND_API"
```

## Troubleshooting

### Service Unreachable

```yaml
- name: Diagnose DevMind connectivity
  if: failure()
  run: |
    echo "Testing DevMind connectivity..."
    ping -c 3 devmind.example.com || echo "Ping failed"
    curl -v https://devmind.example.com/health || echo "Connection failed"
```

### Slow Predictions

```yaml
- name: Monitor DevMind performance
  run: |
    time curl -s -X POST "$DEVMIND_API/api/v1/test-intelligence/select" \
      -H "Content-Type: application/json" \
      -d @payload.json > /dev/null
```

### Invalid Responses

```yaml
- name: Validate DevMind response
  run: |
    RESPONSE=$(curl -s -X POST "$DEVMIND_API/api/v1/test-intelligence/select" -d @payload.json)

    if ! echo $RESPONSE | jq -e '.selected_tests' > /dev/null 2>&1; then
      echo "Invalid response from DevMind:"
      echo $RESPONSE
      exit 1
    fi
```

## Integration Checklist

- [ ] DevMind service is deployed and healthy
- [ ] API endpoints are accessible from GitHub Actions runners
- [ ] Firewall rules allow HTTPS (port 443) to DevMind
- [ ] (Optional) API authentication is configured with secrets
- [ ] Test workflow manually with `/workflow_dispatch`
- [ ] Monitor first 5 workflow runs for issues
- [ ] Add error handling for timeout/unavailability
- [ ] Document DevMind integration in team wiki
- [ ] Train team on interpreting DevMind recommendations

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
