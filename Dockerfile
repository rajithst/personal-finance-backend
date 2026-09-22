# Use official lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install system dependencies needed for compiling packages and running MySQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create a non-root system user for security
RUN groupadd -r appgroup && useradd -r -m -g appgroup -u 1000 appuser

# Copy application source code
COPY . /app/

# Collect static files for WhiteNoise
RUN SECRET_KEY="build-static-placeholder" \
    ALLOWED_HOSTS="*" \
    ENV="dev" \
    DEBUG="True" \
    python manage.py collectstatic --noinput

# Set ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose default Cloud Run port
EXPOSE 8080

# Run Gunicorn binding dynamically to $PORT provided by Cloud Run
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 core.wsgi:application
