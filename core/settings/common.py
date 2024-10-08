"""
Django settings for personalfinance project.

Generated by 'django-admin startproject' using Django 5.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""
from datetime import timedelta
from pathlib import Path
import os
import environ
import io
from google.cloud import secretmanager
from urllib.parse import urlparse

env = environ.Env(DEBUG=(bool, False))

BASE_DIR = Path(__file__).resolve().parent.parent.parent

RUNNING_ENV = os.environ.get('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
ENV = 'prod' if RUNNING_ENV == 'core.settings.prod' else 'dev'
project_id = os.environ.get('PROJECT_ID')
BUCKET_NAME = "%s.appspot.com" % project_id
DEBUG = True
if ENV == 'prod':
    DEBUG = False
    gcloud_project = os.environ.get('GOOGLE_CLOUD_PROJECT', None)
    if os.environ.get('GOOGLE_CLOUD_PROJECT', None):
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        client = secretmanager.SecretManagerServiceClient()
        settings_name = os.environ.get('SETTINGS_NAME', 'django_settings')
        name = f'projects/{project_id}/secrets/{settings_name}/versions/latest'
        payload = client.access_secret_version(name=name).payload.data.decode('UTF-8')
        env.read_env(io.StringIO(payload))
    else:
        raise Exception('No local .env or GOOGLE_CLOUD_PROJECT detected. No secrets found.')

    APPENGINE_URL = os.environ.get("APPENGINE_URL", default=None)
    if APPENGINE_URL:
        if not urlparse(APPENGINE_URL).scheme:
            APPENGINE_URL = f"https://{APPENGINE_URL}"

        allowed_host_1 = urlparse(APPENGINE_URL).netloc
        ALLOWED_HOSTS = [allowed_host_1]
        if '-dot-' in allowed_host_1:
            allowed_host_2 = allowed_host_1.replace('-dot-', '.')
            ALLOWED_HOSTS.append(allowed_host_2)
        CSRF_TRUSTED_ORIGINS = [APPENGINE_URL]
        SECURE_SSL_REDIRECT = False
    else:
        ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'djoser',
    "transactions",
    "investments",
    "oauth"
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]


ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

AUTH_USER_MODEL = "oauth.User"

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'SIGNING_KEY': env('SECRET_KEY') if ENV == 'prod' else 'mySigningKey',
    'TOKEN_OBTAIN_SERIALIZER': "oauth.serializers.TokenObtainPairSerializer",
}

DJOSER = {
    'SERIALIZERS': {
        'user_create': 'oauth.serializers.UserCreateSerializer',
    },
}

INTERNAL_IPS = [
    "127.0.0.1",
]

CORS_ALLOWED_ORIGINS = ['http://localhost:4200', 'https://personal-finance-425009.uc.r.appspot.com']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler'
        },
        # 'file': {
        #     'class': 'logging.FileHandler',
        #     'filename': 'general.log'
        # }
    },
    'loggers': {
        'django.db.backends': {
        }
    },
    'formatters': {
        'verbose': {
            'format': '{asctime} - ({levelname}) - {name} - {message}',
            'style': '{'
        }
    }
}
