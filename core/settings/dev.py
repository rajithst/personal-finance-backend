from .common import *
from django.core.management.utils import get_random_secret_key

DEBUG = True

SECRET_KEY = get_random_secret_key()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'personal_finance',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'Rst@6507'
    }
}
ALLOWED_HOSTS = []
