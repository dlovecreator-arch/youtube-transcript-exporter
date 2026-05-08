FROM python:3.11-slim

LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="YouTube Transcript Exporter - Production Grade"
LABEL version="1.0"

# Set working directory
WORKDIR /app

# Install system dependencies (if needed in future)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/db /app/out /app/markdown /app/logs

# Make scripts executable
RUN chmod +x *.sh src/*.py *.py 2>/dev/null || true

# Set Python to unbuffered mode for proper logging
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN useradd -m -u 1000 exporter && chown -R exporter:exporter /app
USER exporter

# Default command
CMD ["python3", "system_health_check.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 system_health_check.py > /dev/null 2>&1 || exit 1
