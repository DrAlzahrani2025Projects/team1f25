# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for continuous integration and continuous deployment (CI/CD). The pipeline automatically runs tests, builds Docker images, and performs quality checks on every push and pull request.

## Workflows

### 1. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

**Full pipeline with 6 jobs:**

#### Job 1: Unit Tests
- **Trigger:** All pushes and PRs
- **Speed:** ~30 seconds
- **Purpose:** Fast validation of core logic
- **Actions:**
  - Install Python 3.12 and dependencies
  - Run unit tests with `python run_pytest.py unit`
  - Generate coverage report
  - Upload coverage to Codecov

#### Job 2: Integration Tests
- **Trigger:** Pushes to main/fresh-start/develop (not PRs)
- **Speed:** ~2-5 minutes
- **Purpose:** Test with real APIs
- **Requirements:** `GROQ_API_KEY` secret
- **Actions:**
  - Run integration tests with real Groq API
  - Continue build even if API is temporarily down

#### Job 3: Docker Build Test
- **Trigger:** All pushes and PRs (after unit tests pass)
- **Speed:** ~1-2 minutes
- **Purpose:** Validate Docker builds
- **Actions:**
  - Build production Dockerfile
  - Build test Dockerfile
  - Run unit tests inside container
  - Verify production container starts correctly

#### Job 4: Code Quality
- **Trigger:** All pushes and PRs
- **Speed:** ~30 seconds
- **Purpose:** Maintain code standards
- **Tools:**
  - **Black** - Code formatting
  - **isort** - Import sorting
  - **flake8** - Linting
  - **mypy** - Type checking
- **Note:** Failures don't block merge (warnings only)

#### Job 5: Security Scan
- **Trigger:** All pushes and PRs
- **Speed:** ~30 seconds
- **Purpose:** Detect security vulnerabilities
- **Tools:**
  - **Safety** - Check dependencies for known vulnerabilities
  - **Bandit** - Static security analysis
- **Note:** Results are warnings only

#### Job 6: Notify
- **Trigger:** Always runs after other jobs
- **Purpose:** Summary of pipeline results
- **Actions:** Report success/failure status

### 2. Quick Tests (`.github/workflows/quick-test.yml`)

**Lightweight workflow for fast feedback:**

- **Trigger:** All pushes and PRs
- **Speed:** ~20 seconds
- **Purpose:** Quick validation
- **Actions:** Only run unit tests

## Setup

### Required Secrets

Add these secrets in GitHub repository settings (`Settings` → `Secrets and variables` → `Actions`):

| Secret | Required For | Description |
|--------|-------------|-------------|
| `GROQ_API_KEY` | Integration tests | Groq API key for LLM testing |

### Optional Secrets

| Secret | Purpose |
|--------|---------|
| `CODECOV_TOKEN` | Enhanced coverage reporting |
| `SLACK_WEBHOOK` | Slack notifications |

## Workflow Triggers

### Automatic Triggers

```yaml
# Run on push to specific branches
on:
  push:
    branches: [ main, fresh-start, develop ]

# Run on pull requests
on:
  pull_request:
    branches: [ main, fresh-start ]

# Allow manual trigger
on:
  workflow_dispatch:
```

### Manual Trigger

1. Go to **Actions** tab in GitHub
2. Select **CI/CD Pipeline** workflow
3. Click **Run workflow**
4. Select branch and run

## Status Badges

Add to README.md:

```markdown
![CI/CD Pipeline](https://github.com/DrAlzahrani2025Projects/team1f25/workflows/CI%2FCD%20Pipeline/badge.svg)
![Quick Tests](https://github.com/DrAlzahrani2025Projects/team1f25/workflows/Quick%20Tests/badge.svg)
```

## Local Testing

Before pushing, test locally to match CI environment:

```bash
# Run what CI runs
python run_pytest.py unit              # Unit tests
python run_pytest.py integration       # Integration tests (needs API key)

# Docker tests
docker build -f Dockerfile.test -t team1f25-tests .
docker run --rm team1f25-tests python run_pytest.py unit

# Code quality
black --check core/ ui/ tests/
flake8 core/ ui/ tests/ --max-line-length=120
```

## Viewing Results

### GitHub Actions UI

1. Go to **Actions** tab
2. Click on a workflow run
3. View job details and logs
4. Download artifacts (coverage reports, etc.)

### Status Checks on PRs

- ✅ Green checkmark = All tests passed
- ❌ Red X = Tests failed (click for details)
- 🟡 Yellow dot = Tests running

### Coverage Reports

Coverage uploaded to Codecov (if configured):
- View at `https://codecov.io/gh/DrAlzahrani2025Projects/team1f25`
- See coverage trends over time
- View uncovered lines

## Branch Protection Rules

Recommended settings for `main` branch:

1. Go to `Settings` → `Branches` → `Add rule`
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Select: `Quick Unit Tests` (required)
   - Select: `Docker Build Test` (optional)
   - ✅ Require pull request reviews before merging

## Deployment Flow

```
Developer → Push to feature branch
    ↓
Quick Tests run (20s)
    ↓
Create Pull Request
    ↓
Full CI/CD Pipeline runs:
  - Unit Tests
  - Docker Build
  - Code Quality
  - Security Scan
    ↓
Code Review + Approval
    ↓
Merge to main
    ↓
Full Pipeline runs:
  - All tests
  - Docker Build
  - Code Quality
  - Security Scan
```

## Performance Optimization

### Caching

Pipeline uses caching for faster runs:

```yaml
# Python dependencies cache
uses: actions/setup-python@v4
with:
  cache: 'pip'

# Docker layer cache
cache-from: type=gha
cache-to: type=gha,mode=max
```

**Impact:**
- First run: ~5 minutes
- Cached runs: ~2 minutes

### Parallel Execution

Jobs run in parallel when possible:
- Unit Tests + Code Quality + Security Scan (parallel)
- Integration Tests (after unit tests)
- Docker Build (after unit tests)
- Deploy (after all tests pass)

## Troubleshooting

### Tests Pass Locally But Fail in CI

```bash
# Ensure same Python version
python --version  # Should be 3.12.x

# Check for missing dependencies
pip freeze > current_requirements.txt
diff requirements.txt current_requirements.txt

# Run in clean environment
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
python run_pytest.py unit
```

### Integration Tests Skipping

```bash
# Verify secret is set
# In GitHub: Settings → Secrets → Check GROQ_API_KEY exists

# Test locally
export GROQ_API_KEY="your-key"
python run_pytest.py integration
```

### Docker Build Fails

```bash
# Test Docker build locally
docker build -t team1f25-app .
docker build -f Dockerfile.test -t team1f25-tests .

# Check for large files or missing .dockerignore
du -sh * | sort -h
```

### Slow Pipeline

```yaml
# Skip heavy jobs on draft PRs
if: github.event.pull_request.draft == false

# Skip integration tests on PRs
if: github.event_name == 'push'

# Reduce test matrix
# Run fewer Python versions
```

## Customization

### Add New Job

```yaml
new-job:
  name: My Custom Job
  runs-on: ubuntu-latest
  needs: unit-tests  # Run after unit tests
  
  steps:
    - uses: actions/checkout@v3
    - name: Custom step
      run: echo "Custom action"
```

### Add Slack Notifications

```yaml
- name: Slack Notification
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
  if: always()
```

### Add Email Notifications

```yaml
- name: Send Email
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: CI/CD Results
    body: Build completed with status ${{ job.status }}
  if: failure()
```

## Best Practices

1. **Keep unit tests fast** - Under 1 minute total
2. **Use caching** - Speed up dependency installation
3. **Fail fast** - Run fastest tests first
4. **Parallel execution** - Run independent jobs in parallel
5. **Clear naming** - Use descriptive job and step names
6. **Meaningful comments** - Explain why, not what
7. **Secrets management** - Never hardcode credentials
8. **Branch protection** - Require tests to pass before merge
9. **Regular updates** - Keep actions versions updated
10. **Monitor costs** - GitHub Actions minutes have limits

## Monitoring

### View Workflow Usage

GitHub → Settings → Billing → Actions usage

### Optimize for Free Tier

- Public repos: Unlimited minutes ✅
- Private repos: 2,000 minutes/month
- Optimize by:
  - Skip duplicate jobs
  - Cache dependencies
  - Run heavy tests only on main branch

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Available Actions](https://github.com/marketplace?type=actions)
- [Docker Build Action](https://github.com/docker/build-push-action)
- [Python Setup Action](https://github.com/actions/setup-python)
