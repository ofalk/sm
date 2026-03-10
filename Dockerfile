# Use an official Python runtime as a parent image
FROM python:3.14-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=sm.settings
ENV SECRET_KEY="docker-insecure-key-for-quick-test"
ENV DEBUG=True
ENV ALLOWED_HOSTS="*"
ENV DISABLE_SOCIAL_AUTH=True

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set work directory to the Django app root
WORKDIR /app/sm

# Expose port 8000
EXPOSE 8000

# Start the entrypoint script using its absolute path
CMD ["/app/entrypoint.sh"]
