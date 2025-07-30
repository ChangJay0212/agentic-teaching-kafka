# 🧪 Testing Guide

This document explains how to run the unit tests for the Teaching System beta version.

## Prerequisites

- Docker & Docker Compose installed  
- Your project directory contains `docker-compose.yml` and the `test/` folder with your test cases.

## Running the Tests

1. **Start all services** (Kafka, Zookeeper, Ollama, etc.)  
       docker-compose up -d

2. **Execute the test suite** inside the `agentic-app` container:  
       docker-compose exec agentic-app python -m unittest discover test -v

   - `discover test` tells `unittest` to look in the `test/` directory.  
   - `-v` enables verbose output, showing each test name and result.

## Test Directory Structure

    test/
    ├── test_kafka_client.py
    ├── test_llm_engines.py
    ├── test_models.py
    └── ... other test modules ...

Make sure all your test files are named starting with `test_` so that `unittest discover` can find them.

## Troubleshooting

- If you see connection errors, verify your Kafka and Zookeeper services are healthy.  
- For Docker logs, run:  
       docker-compose logs -f

- To stop services after testing:  
       docker-compose down

---
