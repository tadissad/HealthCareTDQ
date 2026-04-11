"""settings.py – api-gateway"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'health-gateway-secret-key-change-in-prod')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'api_gateway.urls'
WSGI_APPLICATION = 'api_gateway.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
            ],
        },
    },
]

# SQLite cho api-gateway (Account model local)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 giờ

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# JWT Config (phải match auth-service)
JWT_SECRET = os.getenv('JWT_SECRET', 'health-micro-ai-jwt-secret-key-2024')

# ── Healthcare Service URLs ────────────────────────────────────────────────────
AUTH_SERVICE_URL              = os.getenv('AUTH_SERVICE_URL',              'http://auth-service:8000')
PATIENT_SERVICE_URL           = os.getenv('PATIENT_SERVICE_URL',           'http://patient-service:8000')
PHARMACY_SERVICE_URL          = os.getenv('PHARMACY_SERVICE_URL',          'http://pharmacy-service:8000')
MEDICAL_CATALOG_SERVICE_URL   = os.getenv('MEDICAL_CATALOG_SERVICE_URL',   'http://medical-catalog-service:8000')
PRESCRIPTION_SERVICE_URL      = os.getenv('PRESCRIPTION_SERVICE_URL',      'http://prescription-service:8000')
DISPENSING_SERVICE_URL        = os.getenv('DISPENSING_SERVICE_URL',        'http://dispensing-service:8000')
MEDICAL_REVIEW_SERVICE_URL    = os.getenv('MEDICAL_REVIEW_SERVICE_URL',    'http://medical-review-service:8000')
CLINICAL_ADVISORY_SERVICE_URL = os.getenv('CLINICAL_ADVISORY_SERVICE_URL', 'http://clinical-advisory-service:8000')
TREATMENT_REC_SERVICE_URL     = os.getenv('TREATMENT_REC_SERVICE_URL',     'http://treatment-recommender-service:8000')
