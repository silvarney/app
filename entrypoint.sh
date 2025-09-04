#!/bin/bash

# Exit on any error
set -e

# Function to wait for database
wait_for_db() {
    echo "Waiting for database..."
    while ! nc -z $DB_HOST $DB_PORT; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
    echo "Database is up - continuing..."
}

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z redis 6379; do
        echo "Redis is unavailable - sleeping"
        sleep 1
    done
    echo "Redis is up - continuing..."
}

# Wait for services
if [ "$DATABASE_URL" ]; then
    wait_for_db
fi

wait_for_redis

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "Creating superuser if it doesn't exist..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Compile messages (if using internationalization)
if [ -d "locale" ]; then
    echo "Compiling messages..."
    python manage.py compilemessages
fi

echo "Starting application..."
exec "$@"