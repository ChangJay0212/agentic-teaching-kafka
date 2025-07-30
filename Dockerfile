# Intelligent Teaching System V1 - Main Dockerfile
FROM python:3.11-slim

LABEL maintainer="Teaching System Team"
LABEL description="Agentic Teaching Kafka System V1"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Set health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "from src.core.kafka_client import KafkaClient; import sys; sys.exit(0 if KafkaClient().health_check() else 1)"

# Expose port (if needed)
EXPOSE 8000

# Default keep container running, waiting for exec commands
CMD ["tail", "-f", "/dev/null"]
