#!/bin/bash
set -e

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Load initial fixtures
echo "Loading default fixtures..."
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

# Generate a random password and create/update admin user
ADMIN_PASSWORD=$(python -c "import secrets; import string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(16)))")

echo "----------------------------------------------------------------"
echo "                      ADMIN LOGIN DETAILS                       "
echo "----------------------------------------------------------------"
echo "Username: admin"
echo "Password: $ADMIN_PASSWORD"
echo "----------------------------------------------------------------"

# Create superuser using a Python script to handle existence check
python <<EOF
import os
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = 'admin'
email = 'admin@example.com'
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

# Start the application server
echo "Starting server..."
python manage.py runserver 0.0.0.0:8000
