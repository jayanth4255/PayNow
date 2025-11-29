"""
WSGI config for PAYMENT project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PAYMENT.settings')

# Fail-safe: Run collectstatic on startup
try:
    call_command('collectstatic', interactive=False)
except Exception as e:
    print(f"Error collecting static files: {e}")

application = get_wsgi_application()
