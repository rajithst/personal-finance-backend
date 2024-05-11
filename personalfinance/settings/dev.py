from .common import *
DEBUG = True

SECRET_KEY = 'django-insecure-$h=7%)@t-3g8da+!i$3m7$(z9+jyy*1bnv#&2w-lw^v1o7qk3b'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'personal_finance',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'Rst@6507@JP'
    }
}
ALLOWED_HOSTS = ["*"]
print('ALLOWED Hosts: ', ALLOWED_HOSTS)