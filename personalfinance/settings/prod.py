from .common import *

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DBNAME'),
        'HOST': os.environ.get('DBHOST'),
        'USER': os.environ.get('DBUSER'),
        'PASSWORD': os.environ.get('DBPASS'),
        'OPTIONS': {'sslmode': 'require'},
    }
}

ALLOWED_HOSTS = ['pfbackend.azurewebsites.net', '127.0.0.1', '169.254.130.6']
CSRF_TRUSTED_ORIGINS = ['pfbackend.azurewebsites.net']
SECURE_SSL_REDIRECT = True
print('ALLOWED Hosts: ', ALLOWED_HOSTS)
