# Docker Guide

## Overview

This project provides two Docker configurations:
- **Dockerfile** - Production application container
- **Dockerfile.test** - Test execution container

## Production Container (Dockerfile)

### Build

```bash
docker build -f docker/Dockerfile -t team1f25-app .
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
docker build -f docker/Dockerfile.test -t team1f25-tests .
```

### Run Tests

```bash
# Run unit tests (default, no API key needed)
docker run --rm team1f25-tests

# Run integration tests (requires API key)
docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python scripts/run_pytest.py integration

# Run end-to-end tests
docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python scripts/run_pytest.py e2e

# Run all pytest tests
docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python scripts/run_pytest.py all

# Run legacy tests
docker run --rm -e GROQ_API_KEY="your-key" team1f25-tests python scripts/run_pytest.py legacy
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
    build:
      context: .
      dockerfile: docker/Dockerfile
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
      dockerfile: docker/Dockerfile.test
    image: team1f25-tests
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    command: python scripts/run_pytest.py all
```

### Usage

```bash
# Run app
docker-compose up app

# Run tests
docker-compose run --rm tests

# Run specific test type
docker-compose run --rm tests python scripts/run_pytest.py unit

# Clean up
docker-compose down
```
