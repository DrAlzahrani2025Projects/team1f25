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
