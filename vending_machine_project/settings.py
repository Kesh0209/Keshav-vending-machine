from pathlib import Path
import os
import dj_database_url

# ------------------------------
# Base directory setup
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------
# Security & Debug
# ------------------------------
SECRET_KEY = 'django-insecure-testkey123'
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# ------------------------------
# Installed Apps
# ------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'machine_app',
]

# ------------------------------
# Middleware
# ------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # for static files on Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ------------------------------
# URLs and WSGI
# ------------------------------
ROOT_URLCONF = 'vending_machine_project.urls'
WSGI_APPLICATION = 'vending_machine_project.wsgi.application'

# ------------------------------
# Templates
# ------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# ------------------------------
# Databases
# ------------------------------
# Default: SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# If DATABASE_URL is set (Render), switch to PostgreSQL
if os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        default='postgres://user:password@host:port/database_name',
        conn_max_age=600
    )

# ------------------------------
# Passwords & Auth
# ------------------------------
AUTH_PASSWORD_VALIDATORS = []

# ------------------------------
# Localization
# ------------------------------
LANGUAGE_CODE = 'en-uk'
TIME_ZONE = 'Indian/Mauritius'
USE_I18N = True
USE_TZ = True

# ------------------------------
# Static & Media Files
# ------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)

# ------------------------------
# Security (for Render)
# ------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True

    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_MANIFEST_STRICT = False
    WHITENOISE_ALLOW_ALL_ORIGINS = True

# ------------------------------
# Default field type
# ------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
