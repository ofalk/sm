FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DJANGO_SETTINGS_MODULE=sm.settings
ENV SECRET_KEY="docker-insecure-key-for-quick-test"
ENV DEBUG=True
ENV ALLOWED_HOSTS="*"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/

RUN chmod +x /app/entrypoint.sh

WORKDIR /app/sm

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
