"""
WSGI config for personalfinance project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from google.appengine.api import wrap_wsgi_app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = wrap_wsgi_app(get_wsgi_application())
