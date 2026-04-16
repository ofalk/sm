#!/bin/bash
set -e

# Build paths
BASE_DIR="/app/sm"

wait_for_db() {
    echo "Waiting for database..."
    cd "$BASE_DIR"
    for i in {1..30}; do
        if python3 manage.py check >/dev/null 2>&1; then
            echo "Database is ready!"
            return 0
        fi
        echo "Database not ready yet (attempt $i)..."
        sleep 2
    done
    echo "Database timed out!"
    exit 1
}

# If we're called with 'migrate', 'loaddata', 'collectstatic', or 'ensure_admin'
# then only run those and exit.
case "$1" in
migrate)
    wait_for_db
    echo "Running migrations..."
    python3 manage.py migrate --noinput
    exit 0
    ;;
loaddata)
    wait_for_db
    echo "Loading default fixtures..."
    fixtures=(
        "status/fixtures/01_initial.yaml"
        "vendor/fixtures/01_initial.yaml"
        "operatingsystem/fixtures/01_initial.yaml"
        "patchtime/fixtures/01_initial.yaml"
        "domain/fixtures/01_initial.yaml"
        "location/fixtures/01_initial.yaml"
        "servermodel/fixtures/01_initial.yaml"
        "clusterpackagetype/fixtures/01_initial.yaml"
        "sm/fixtures/02_groups.yaml"
        "clustersoftware/fixtures/01_initial.yaml"
    )
    for fixture in "${fixtures[@]}"; do
        echo "Loading $fixture..."
        python3 manage.py loaddata "$fixture"
    done
    exit 0
    ;;
collectstatic)
    echo "Collecting static files..."
    cd "$BASE_DIR" && python3 manage.py collectstatic --noinput
    exit 0
    ;;
ensure_admin)
    wait_for_db
    echo "Ensuring admin user exists..."
    # If ADMIN_PASSWORD is provided in ENV, use it. Otherwise generate random.
    if [ -z "$ADMIN_PASSWORD" ]; then
        export ADMIN_PASSWORD=$(python3 -c "import secrets; import string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(16)))")
        echo "Generated random password: $ADMIN_PASSWORD"
    else
        echo "Using provided ADMIN_PASSWORD from environment"
    fi

    # Ensure SocialApps only if the module is installed
    python3 <<'EOF'
import os
import django
import sys
from django.apps import apps

django.setup()

# Check if socialaccount is installed
if not apps.is_installed('allauth.socialaccount'):
    print("allauth.socialaccount not installed, skipping SocialApp setup")
    sys.exit(0)

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('ADMIN_USERNAME', 'admin')
email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
password = os.environ.get('ADMIN_PASSWORD')

if password and password != 'REPLACE_WITH_REAL_ADMIN_PASSWORD':
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"Superuser '{username}' created successfully.")
    else:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        print(f"Password for superuser '{username}' updated.")

site = Site.objects.get_current()

# Ensure Google SocialApp
google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
google_secret = os.environ.get('GOOGLE_SECRET')
if google_client_id and google_secret and google_client_id not in ['REPLACE_WITH_REAL_GOOGLE_ID', 'CHANGE_ME']:
    try:
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': google_client_id,
                'secret': google_secret
            }
        )
        if not created:
            if app.client_id != google_client_id or app.secret != google_secret:
                app.client_id = google_client_id
                app.secret = google_secret
                app.save()
                print("Google SocialApp updated.")
        else:
            print("Google SocialApp created.")
        app.sites.add(site)
    except Exception as e:
        print(f"Error setting up Google SocialApp: {e}")

# Ensure Authentik SocialApp
authentik_client_id = os.environ.get('AUTHENTIK_CLIENT_ID')
authentik_secret = os.environ.get('AUTHENTIK_SECRET')
authentik_url = os.environ.get('AUTHENTIK_URL', 'https://auth.localghost.com/application/o/sm/.well-known/openid-configuration')

if authentik_client_id and authentik_secret and authentik_client_id not in ['REPLACE_WITH_REAL_AUTHENTIK_ID', 'CHANGE_ME']:
    try:
        app, created = SocialApp.objects.get_or_create(
            provider='openid_connect',
            provider_id='authentik',
            defaults={
                'name': 'Authentik',
                'client_id': authentik_client_id,
                'secret': authentik_secret,
                'settings': {'server_url': authentik_url}
            }
        )
        if not created:
            if app.client_id != authentik_client_id or app.secret != authentik_secret or app.settings.get('server_url') != authentik_url:
                app.client_id = authentik_client_id
                app.secret = authentik_secret
                app.settings = {'server_url': authentik_url}
                app.save()
                print("Authentik SocialApp updated.")
        else:
            print("Authentik SocialApp created.")
        app.sites.add(site)
    except Exception as e:
        print(f"Error setting up Authentik SocialApp: {e}")
EOF
    exit 0
    ;;
esac

# Default: Start the application server
wait_for_db
echo "Starting server..."
cd "$BASE_DIR" && gunicorn --bind 0.0.0.0:8000 sm.wsgi:application
