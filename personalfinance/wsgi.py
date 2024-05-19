"""
WSGI config for personalfinance project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
c1 = 'PRODUCTION' in os.environ and os.environ.get('PRODUCTION')
settings_module = 'personalfinance.settings.prod' if c1 else 'personalfinance.settings.dev'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
application = get_wsgi_application()
