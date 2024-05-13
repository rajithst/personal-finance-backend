from .common import *

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = [os.environ['WEBSITE_HOSTNAME']]
CSRF_TRUSTED_ORIGINS = ['https://' + os.environ['WEBSITE_HOSTNAME']]
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': os.environ.get('DBNAME'),
        'HOST': os.environ.get('DBHOST'),
        'USER': os.environ.get('DBUSER'),
        "PORT": os.environ.get('DBPORT'),
        'PASSWORD': os.environ.get('DBPASS'),
        'OPTIONS': {
                    'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}

print('ALLOWED Hosts PROD: ', ALLOWED_HOSTS)