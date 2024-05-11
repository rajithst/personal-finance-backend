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

ALLOWED_HOSTS = ['pfbackend.azurewebsites.net', os.environ['WEBSITE_HOSTNAME']]
logging.info('allowd hosts: ', ALLOWED_HOSTS)
logging.info('os.environ WEBSITE_HOSTNAME', os.environ['WEBSITE_HOSTNAME'])
CSRF_TRUSTED_ORIGINS = ['https://' + os.environ['WEBSITE_HOSTNAME']]
SECURE_SSL_REDIRECT = True

