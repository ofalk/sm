FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DJANGO_SETTINGS_MODULE=sm.settings
# SECRET_KEY is intentionally NOT baked into the image: supply it at runtime
# (docker run -e SECRET_KEY=...). Settings refuse to start without it.
ENV DEBUG=False
ENV ALLOWED_HOSTS="localhost,127.0.0.1"

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

# Bake static files into the image. A throwaway key is generated only for this
# build step; it is never written to the image environment.
RUN SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')" \
    python3 manage.py collectstatic --noinput

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
