
from .common import *

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'HOST': env('HOST'),
        'USER': env('USER'),
        'PASSWORD': env('PASSWORD'),
    }
}
SECRET_KEY = env('SECRET_KEY')


