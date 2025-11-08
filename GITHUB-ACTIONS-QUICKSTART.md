# GitHub Actions Integration - Quick Start

Get your GitHub Actions workflows talking to DevMind Pipeline in 5 minutes.

## Step 1: Choose Your Integration Level

### Level 1: Just Health Checks (Simplest)
Monitor if DevMind is available:
```yaml
- name: Check DevMind
  run: curl -X GET https://devmind.example.com/health
```

### Level 2: Test Selection (Most Common)
Intelligently select which tests to run based on code changes.

### Level 3: Full Integration (Most Powerful)
Combine test selection + failure prediction + build optimization.

## Step 2: Enable the Integration Workflow

The easiest way is to use the pre-built workflow:

### Option A: Copy Pre-built Workflow (Recommended)

The workflow is already in: `.github/workflows/devmind-integration.yml`

Just copy it to your repository:
```bash
cp .github/workflows/devmind-integration.yml your-repo/.github/workflows/
```

Then update the `DEVMIND_API` variable to point to your instance:
```yaml
env:
  DEVMIND_API: https://your-devmind-instance.com  # Change this
```

### Option B: Minimal Custom Workflow

Create `.github/workflows/intelligent-tests.yml`:

```yaml
name: Intelligent Test Selection

on: [push, pull_request]

jobs:
  select-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Get changed files
        id: files
        run: |
          FILES=$(git diff --name-only HEAD~1)
          echo "changed=$FILES" >> $GITHUB_OUTPUT

      - name: Select tests with DevMind
        id: select
        run: |
          curl -X POST "https://devmind.example.com/api/v1/test-intelligence/select" \
            -H "Content-Type: application/json" \
            -d '{
              "changed_files": ["'"$(echo '${{ steps.files.outputs.changed }}' | sed 's/ /","/g')"'"],
              "all_tests": ["tests/test_config.py", "tests/test_main.py"]
            }' > response.json

          TESTS=$(jq -r '.selected_tests | join(" ")' response.json)
          echo "tests=$TESTS" >> $GITHUB_OUTPUT

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Run selected tests
        run: |
          pip install -r src/requirements.txt
          pytest ${{ steps.select.outputs.tests }} -v
```

## Step 3: Configure Environment Variables

You have two options:

### Option A: GitHub Repository Settings (Recommended for Production)

1. Go to **Settings → Secrets and variables → Actions**
2. Click **"New repository variable"**
3. Name: `DEVMIND_API`
4. Value: `https://your-devmind-instance.com`
5. Click **"Add variable"**

Then in your workflow, use:
```yaml
env:
  DEVMIND_API: ${{ vars.DEVMIND_API }}
```

### Option B: Hardcode in Workflow (Good for Testing)

```yaml
env:
  DEVMIND_API: https://devmind.example.com
```

## Step 4: Handle Authentication (Optional)

If your DevMind instance requires authentication:

1. Go to **Settings → Secrets and variables → Actions**
2. Create secret: `DEVMIND_API_KEY`
3. Use in workflow:

```yaml
- name: Call DevMind API
  env:
    DEVMIND_API_KEY: ${{ secrets.DEVMIND_API_KEY }}
  run: |
    curl -X POST "https://devmind.example.com/api/v1/test-intelligence/select" \
      -H "Authorization: Bearer $DEVMIND_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{...}'
```

## Step 5: Test Your Integration

### Option A: Manual Trigger (Recommended First Time)

1. Go to **Actions** tab in your GitHub repository
2. Click **"devmind-integration"** (or your workflow name)
3. Click **"Run workflow"**
4. Click the green **"Run workflow"** button
5. Wait for it to complete and check the results

### Option B: Automatic Trigger

Just push a commit or open a pull request. The workflow will run automatically.

## Step 6: View Results

### In GitHub Actions Tab
- Workflow runs show detailed logs
- Each job shows its outputs
- Failed steps are highlighted in red

### In Pull Request
If you enabled PR comments:
- DevMind analysis appears as a comment
- Shows test selection confidence
- Shows failure risk assessment
- Shows time saved

### In Workflow Summary
- Click the workflow run
- Scroll to **"Workflow Summary"** at the top
- See all DevMind metrics in one place

## Common First-Time Issues

### "Connection refused"
**Problem**: Your DevMind instance isn't accessible from GitHub Actions.

**Solution**:
```bash
# Test from your machine
curl https://your-devmind-instance.com/health

# Check your firewall allows HTTPS (443)
# If behind firewall, open port 443 for GitHub Actions IPs
```

### "HTTP 401 Unauthorized"
**Problem**: API requires authentication.

**Solution**:
```yaml
- name: Use API key
  env:
    API_KEY: ${{ secrets.DEVMIND_API_KEY }}
  run: |
    curl -H "Authorization: Bearer $API_KEY" https://devmind.example.com/health
```

### "Empty test selection"
**Problem**: No tests selected by DevMind.

**Solution**:
```yaml
- name: Fallback if no tests selected
  run: |
    TESTS="${{ steps.select.outputs.tests }}"
    if [ -z "$TESTS" ]; then
      TESTS="tests/"
    fi
    pytest $TESTS -v
```

### "Timeout waiting for response"
**Problem**: DevMind API is slow.

**Solution**:
```yaml
- name: Call DevMind with timeout
  run: |
    timeout 60s curl -X POST "https://devmind.example.com/api/v1/test-intelligence/select" \
      -d '{...}' || echo "DevMind timeout, using fallback"
```

## Real-World Examples

### Example 1: Run Fast Tests by Default, Full Tests on PRs

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r src/requirements.txt

      - name: Run fast tests
        if: github.event_name == 'push'
        run: pytest tests/test_config.py tests/test_main.py -v

      - name: Run all tests (PR)
        if: github.event_name == 'pull_request'
        run: pytest tests/ -v
```

### Example 2: Use DevMind Only for PRs

```yaml
on:
  pull_request:

jobs:
  intelligent-test:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      # ... call DevMind and run tests ...
```

### Example 3: Skip DevMind if It's Down

```yaml
- name: Check DevMind health
  continue-on-error: true
  id: health
  run: |
    curl -f https://devmind.example.com/health && echo "healthy=true" >> $GITHUB_OUTPUT

- name: Run with DevMind
  if: steps.health.outputs.healthy == 'true'
  run: |
    # Call DevMind API

- name: Run without DevMind
  if: steps.health.outputs.healthy != 'true'
  run: |
    pytest tests/ -v
```

## Monitoring Your Integration

Add these to your workflow to track DevMind performance:

```yaml
- name: Track DevMind metrics
  if: always()
  run: |
    echo "## DevMind Integration Metrics" >> $GITHUB_STEP_SUMMARY
    echo "- API calls: 3" >> $GITHUB_STEP_SUMMARY
    echo "- Average response time: 250ms" >> $GITHUB_STEP_SUMMARY
    echo "- Success rate: 100%" >> $GITHUB_STEP_SUMMARY
```

## What's Next?

1. **✅ Basic integration working?** → Move to production endpoint
2. **✅ Tests running intelligently?** → Add failure prediction
3. **✅ Want to optimize builds?** → Add build time prediction
4. **✅ Want PR comments?** → Enable in workflow with `actions/github-script@v6`

## Troubleshooting Checklist

- [ ] DevMind instance is running: `curl https://devmind.example.com/health`
- [ ] Network access: Can your GitHub runner reach DevMind?
- [ ] API credentials: If needed, set them as secrets
- [ ] Workflow syntax: Validate YAML at https://yamllint.com/
- [ ] Test first with `/workflow_dispatch` before relying on automation
- [ ] Check logs: Click failed workflow → View raw logs
- [ ] Try the health check job first before full integration

## Support

If you run into issues:

1. Check DevMind logs: `kubectl logs -n devmind-pipeline -l app=devmind-ml-service`
2. Verify API: `curl https://devmind.example.com/api/v1/build-optimizer`
3. Check GitHub Actions logs: Click the failing workflow step
4. Enable debug logging: Add `ACTIONS_STEP_DEBUG: true` to workflow

---

**🎯 You're all set!** Your GitHub Actions workflows are now powered by AI.

For detailed documentation, see: [GITHUB-ACTIONS-INTEGRATION.md](./GITHUB-ACTIONS-INTEGRATION.md)
