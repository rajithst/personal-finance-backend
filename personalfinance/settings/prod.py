
from .common import *

DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'personal_finance',
        'HOST': '/cloudsql/personal-finance-425009:us-central1:coincraft',
        'USER': 'db_admin',
        'PASSWORD': 'Rst@6507'
    }
}


