from .common import *
DEBUG = True

SECRET_KEY = 'django-insecure-$h=7%)@t-3g8da+!i$3m7$(z9+jyy*1bnv#&2w-lw^v1o7qk3b'
c1 = 'PRODUCTION' in os.environ and os.environ.get('PRODUCTION')
db_settings = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'personal_finance',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'Rst@6507@JP'
        }
if c1:
    db_settings = {
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
DATABASES = {
    'default': db_settings
}
ALLOWED_HOSTS = ["*"]
print('ALLOWED Hosts DEV: ', ALLOWED_HOSTS)
print('DATABASES: ', DATABASES)