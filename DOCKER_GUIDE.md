# Docker Guide

## Overview

This project provides two Docker configurations:
- **Dockerfile** - Production application container
- **Dockerfile.test** - Test execution container

## Production Container (Dockerfile)

### Build

```bash
docker build -t team1f25-app .
```

### Run

```bash
# Run with API key from environment
docker run -p 5001:5001 -e GROQ_API_KEY="your-key" team1f25-app

# Run with data persistence
docker run -p 5001:5001 \
  -e GROQ_API_KEY="your-key" \
  -v $(pwd)/data:/data \
  team1f25-app
```

### Access

Open browser: http://localhost:5001/team1f25

## Test Container (Dockerfile.test)

### Build

```bash
docker build -f Dockerfile.test -t team1f25-tests .
```

### Run Tests

```bash
# Run unit tests (default, no API key needed)
docker run --rm team1f25-tests

# Run integration tests (requires API key)
docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python run_pytest.py integration

# Run end-to-end tests
docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python run_pytest.py e2e

# Run all pytest tests
docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python run_pytest.py all

# Run legacy tests
docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python run_pytest.py legacy
```

### Run with Verbose Output

```bash
# Verbose unit tests
docker run --rm team1f25-tests pytest tests/unit -vv

# Show print statements
docker run --rm team1f25-tests pytest tests/unit -s

# Stop on first failure
docker run --rm team1f25-tests pytest tests/unit -x
```

### Generate Coverage Report

```bash
# Coverage with terminal output
docker run --rm team1f25-tests pytest tests/unit --cov=core --cov-report=term

# Coverage with detailed report
docker run --rm team1f25-tests pytest tests/unit --cov=core --cov-report=term-missing

# Save coverage HTML report (requires volume mount)
docker run --rm -v $(pwd)/htmlcov:/app/htmlcov \
  team1f25-tests pytest tests/unit --cov=core --cov-report=html
```

## Docker Compose (Optional)

Create `docker-compose.yml` for easier management:

```yaml
version: '3.8'

services:
  app:
    build: .
    image: team1f25-app
    ports:
      - "5001:5001"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./data:/data
    restart: unless-stopped

  tests:
    build:
      context: .
      dockerfile: Dockerfile.test
    image: team1f25-tests
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    command: python run_pytest.py all
```

### Usage

```bash
# Run app
docker-compose up app

# Run tests
docker-compose run --rm tests

# Run specific test type
docker-compose run --rm tests python run_pytest.py unit

# Clean up
docker-compose down
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes (for app) | Groq API key for LLM |
| `GROQ_API_KEY` | No (for unit tests) | Only needed for integration tests |
| `PYTHONPATH` | Auto-set | Set to `/app` in test container |

## Troubleshooting

### Tests fail with "Module not found"

```bash
# Rebuild the test image
docker build -f Dockerfile.test -t team1f25-tests . --no-cache
```

### Integration tests skip

```bash
# Make sure API key is set
docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python run_pytest.py integration
```

### Port already in use

```bash
# Find and stop the container
docker ps
docker stop <container-id>

# Or use a different port
docker run -p 5002:5001 -e GROQ_API_KEY="your-key" team1f25-app
```

### Permission denied on volume mount

```bash
# On Linux/Mac, ensure correct permissions
chmod -R 755 data/

# On Windows WSL, use WSL path
docker run -p 5001:5001 \
  -v /mnt/c/Users/<your_loc>/team1f25/data:/data \
  -e GROQ_API_KEY="your-key" \
  team1f25-app
```

## Best Practices

### Development Workflow

1. **Build once:**
   ```bash
   docker build -t team1f25-app .
   docker build -f Dockerfile.test -t team1f25-tests .
   ```

2. **Run unit tests frequently:**
   ```bash
   docker run --rm team1f25-tests
   ```

3. **Run integration tests before commit:**
   ```bash
   docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python run_pytest.py all
   ```

4. **Test the app locally:**
   ```bash
   docker run -p 5001:5001 -e GROQ_API_KEY="your-key" team1f25-app
   ```

### CI/CD Integration

```yaml
# GitHub Actions example
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build test image
        run: docker build -f Dockerfile.test -t team1f25-tests .
      
      - name: Run unit tests
        run: docker run --rm team1f25-tests python run_pytest.py unit
      
      - name: Run integration tests
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
        run: docker run --rm -e GROQ_API_KEY="${GROQ_API_KEY}" team1f25-tests python run_pytest.py integration
```

## Quick Reference

```bash
# Production
docker build -t team1f25-app .
docker run -p 5001:5001 -e GROQ_API_KEY="key" team1f25-app

# Tests (unit - fast)
docker build -f Dockerfile.test -t team1f25-tests .
docker run --rm team1f25-tests

# Tests (integration - requires API key)
docker run --rm -e GROQ_API_KEY="key" team1f25-tests python run_pytest.py integration

# Tests (all)
docker run --rm -e GROQ_API_KEY="key" team1f25-tests python run_pytest.py all

# Cleanup
docker system prune -a
```
