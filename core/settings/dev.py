from .common import *
from django.core.management.utils import get_random_secret_key
from dev_config import DB_USER, DB_PASSWORD
DEBUG = True

SECRET_KEY = get_random_secret_key()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'personal_finance',
        'HOST': 'localhost',
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD
    }
}
ALLOWED_HOSTS = []
