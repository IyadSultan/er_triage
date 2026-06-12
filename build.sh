#!/usr/bin/env bash
# Render runs this on every deploy. Exit immediately on any error.
set -o errexit

pip install -r requirements.txt

# Collect static files for WhiteNoise to serve.
python manage.py collectstatic --no-input

# Apply database migrations.
python manage.py migrate
