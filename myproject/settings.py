"""
Django settings for the project.

This file is now configured to read all secrets (like SECRET_KEY
and database passwords) from environment variables, which are
provided by the .env file and docker-compose.yml.
"""
import os
from pathlib import Path
from datetime import timedelta
import firebase_admin
from firebase_admin import credentials

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', '0') == '1'

ALLOWED_HOSTS = ['*']


# 1. Define the path to your secret JSON key
# This assumes the file is in your root folder (next to manage.py)
FIREBASE_CRED_PATH = os.path.join(BASE_DIR, 'firebase_credentials.json')

# 2. Initialize the Firebase App
if os.path.exists(FIREBASE_CRED_PATH):
    try:
        # Check if already initialized to prevent errors during hot-reloads
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CRED_PATH)
            firebase_admin.initialize_app(cred)
            print("SUCCESS: Firebase Admin SDK initialized.")
    except Exception as e:
        print(f"ERROR: Failed to initialize Firebase: {e}")
else:
    print(f"WARNING: Firebase credentials file not found at: {FIREBASE_CRED_PATH}")
    print("Push notifications will NOT work.")


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',              
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',  

    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    'corsheaders.middleware.CorsMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'myproject.wsgi.application'


DB_NAME = os.environ.get('POSTGRES_DB')
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
DB_HOST = os.environ.get('POSTGRES_HOST')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': '5432', # Default Postgres port
    }
}



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


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'api.authentication.CookieJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    
    'TOKEN_OBTAIN_SERIALIZER': 'api.serializers.CustomTokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'api.serializers.CustomTokenRefreshSerializer',

    'ACCESS_TOKEN_COOKIE': 'access_token',
}


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500",
    "http://192.168.8.85:8081",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
    "https://119203009014.ngrok-free.app",
]

CORS_ALLOW_CREDENTIALS = True


CSRF_COOKIE_SECURE = False 
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'


BUS_API_KEY = os.environ.get('BUS_API_KEY')

# --- DEBUG PRINT (Delete this later) ---
print("--- EMAIL DEBUG INFO ---")
print(f"HOST: {os.environ.get('EMAIL_HOST')}")
print(f"USER: {os.environ.get('EMAIL_HOST_USER')}")
print(f"TLS: {os.environ.get('EMAIL_USE_TLS')}")
print("------------------------")



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
