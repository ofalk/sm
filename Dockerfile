FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DJANGO_SETTINGS_MODULE=sm.settings
ENV SECRET_KEY="docker-insecure-key-for-quick-test"
ENV DEBUG=False
ENV ALLOWED_HOSTS="*"

ARG APP_VERSION=unknown
ARG APP_MODIFICATION_DATE=unknown
ENV APP_VERSION=$APP_VERSION
ENV APP_MODIFICATION_DATE=$APP_MODIFICATION_DATE

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/

RUN chmod +x /app/entrypoint.sh

WORKDIR /app/sm

# Bake static files into the image
RUN python3 manage.py collectstatic --noinput

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
