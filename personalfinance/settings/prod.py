from .common import *

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ['pfbackend.azurewebsites.net', '127.0.0.1',]
CSRF_TRUSTED_ORIGINS = ['pfbackend.azurewebsites.net']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DBNAME'),
        'HOST': os.environ.get('DBHOST'),
        'USER': os.environ.get('DBUSER'),
        'PASSWORD': os.environ.get('DBPASS'),
    }
}


print('ALLOWED Hosts: ', ALLOWED_HOSTS)
