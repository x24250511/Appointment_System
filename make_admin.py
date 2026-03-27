#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Change this to your registered username
username = 'admin'

try:
    user = User.objects.get(username=username)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✓ {user.username} is now a superuser!")
except User.DoesNotExist:
    print(f"✗ User '{username}' not found. Please register first.")
