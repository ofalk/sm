#!/bin/bash
set -e

# Build paths
BASE_DIR="/app/sm"

# If we're called with 'migrate', 'loaddata', 'collectstatic', or 'ensure_admin'
# then only run those and exit.
case "$1" in
migrate)
    echo "Running migrations..."
    cd "$BASE_DIR" && python3 manage.py migrate --noinput
    exit 0
    ;;
loaddata)
    echo "Loading default fixtures..."
    cd "$BASE_DIR" && {
        python3 manage.py loaddata status/fixtures/01_initial.yaml
        python3 manage.py loaddata vendor/fixtures/01_initial.yaml
        python3 manage.py loaddata operatingsystem/fixtures/01_initial.yaml
        python3 manage.py loaddata patchtime/fixtures/01_initial.yaml
        python3 manage.py loaddata domain/fixtures/01_initial.yaml
        python3 manage.py loaddata location/fixtures/01_initial.yaml
        python3 manage.py loaddata servermodel/fixtures/01_initial.yaml
        python3 manage.py loaddata clusterpackagetype/fixtures/01_initial.yaml
        python3 manage.py loaddata sm/fixtures/02_groups.yaml
        python3 manage.py loaddata clustersoftware/fixtures/01_initial.yaml
    }
    exit 0
    ;;
collectstatic)
    echo "Collecting static files..."
    cd "$BASE_DIR" && python3 manage.py collectstatic --noinput
    exit 0
    ;;
ensure_admin)
    echo "Ensuring admin user exists..."
    # If ADMIN_PASSWORD is provided in ENV, use it. Otherwise generate random.
    if [ -z "$ADMIN_PASSWORD" ]; then
        ADMIN_PASSWORD=$(python3 -c "import secrets; import string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(16)))")
        echo "Generated random password: $ADMIN_PASSWORD"
    else
        echo "Using provided ADMIN_PASSWORD from environment"
    fi

    cd "$BASE_DIR" && python3 <<EOF
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

# Ensure Google SocialApp
google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
google_secret = os.environ.get('GOOGLE_SECRET')
if google_client_id and google_secret:
    from django.contrib.sites.models import Site
    try:
        from allauth.socialaccount.models import SocialApp
        site = Site.objects.get_current()
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': google_client_id,
                'secret': google_secret
            }
        )
        if not created:
            app.client_id = google_client_id
            app.secret = google_secret
            app.save()
        app.sites.add(site)
        print(f"Google SocialApp ensured (created: {created})")
    except ImportError:
        print("allauth.socialaccount not installed, skipping SocialApp setup")
    except Exception as e:
        print(f"Error setting up SocialApp: {e}")
else:
    print("GOOGLE_CLIENT_ID or GOOGLE_SECRET not provided, skipping SocialApp setup")
EOF
    exit 0
    ;;
esac

# Default: Start the application server
echo "Starting server..."
cd "$BASE_DIR" && gunicorn --bind 0.0.0.0:8000 sm.wsgi:application
