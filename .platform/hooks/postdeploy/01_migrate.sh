#!/bin/bash

# Load environment variables from Elastic Beanstalk
if [ -f /opt/elasticbeanstalk/deployment/env ]; then
    source /opt/elasticbeanstalk/deployment/env
fi

# Activate virtual environment
source /var/app/venv/*/bin/activate

# Go to app directory
cd /var/app/current

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput
