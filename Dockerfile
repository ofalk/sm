FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DJANGO_SETTINGS_MODULE=sm.settings

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY sm/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY sm/ /app/

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "sm.wsgi:application"]
