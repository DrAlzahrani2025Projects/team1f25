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
