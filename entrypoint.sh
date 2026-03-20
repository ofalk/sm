#!/bin/bash
set -e

# Build paths
BASE_DIR="/app/sm"

# If we're called with 'migrate', 'loaddata', 'collectstatic', or 'ensure_admin'
# then only run those and exit.
case "$1" in
migrate)
    echo "Running migrations..."
    cd "$BASE_DIR" && python manage.py migrate --noinput
    exit 0
    ;;
loaddata)
    echo "Loading default fixtures..."
    cd "$BASE_DIR" && {
        python manage.py loaddata status/fixtures/01_initial.yaml
        python manage.py loaddata vendor/fixtures/01_initial.yaml
        python manage.py loaddata operatingsystem/fixtures/01_initial.yaml
        python manage.py loaddata patchtime/fixtures/01_initial.yaml
        python manage.py loaddata domain/fixtures/01_initial.yaml
        python manage.py loaddata location/fixtures/01_initial.yaml
        python manage.py loaddata servermodel/fixtures/01_initial.yaml
        python manage.py loaddata clusterpackagetype/fixtures/01_initial.yaml
        python manage.py loaddata sm/fixtures/02_groups.yaml
        python manage.py loaddata clustersoftware/fixtures/01_initial.yaml
    }
    exit 0
    ;;
collectstatic)
    echo "Collecting static files..."
    cd "$BASE_DIR" && python manage.py collectstatic --noinput
    exit 0
    ;;
ensure_admin)
    echo "Ensuring admin user exists..."
    # If ADMIN_PASSWORD is provided in ENV, use it. Otherwise generate random.
    if [ -z "$ADMIN_PASSWORD" ]; then
        ADMIN_PASSWORD=$(python -c "import secrets; import string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(16)))")
        echo "Generated random password: $ADMIN_PASSWORD"
    else
        echo "Using provided ADMIN_PASSWORD from environment"
    fi

    cd "$BASE_DIR" && python <<EOF
import os
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('ADMIN_USERNAME', 'admin')
email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
password = '$ADMIN_PASSWORD'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser '{username}' created successfully.")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"Password for superuser '{username}' updated.")
EOF
    exit 0
    ;;
esac

# Default: Start the application server
echo "Starting server..."
cd "$BASE_DIR" && gunicorn --bind 0.0.0.0:8000 sm.wsgi:application
