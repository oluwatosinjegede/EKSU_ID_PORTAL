from pathlib import Path
import os
import dj_database_url


# --------------------------------------------------
# Base directory
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = ["*"]  # Railway handles domain safety
# --------------------------------------------------
# Core settings
# --------------------------------------------------
SECRET_KEY = 'dev-secret-key'
DEBUG = True
ALLOWED_HOSTS = []

# --------------------------------------------------
# Applications
# --------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    "applications.apps.ApplicationsConfig",

    'accounts',
    'students',
    
    'idcards',
]

# --------------------------------------------------
# Middleware (CLEAN & EXPLICIT)
# --------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # Authentication MUST come before custom auth middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Enforce first-login password change
    'accounts.middleware.PasswordChangeRequiredMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# --------------------------------------------------
# URLs
# --------------------------------------------------
ROOT_URLCONF = 'config.urls'

# --------------------------------------------------
# Templates
# --------------------------------------------------
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

# --------------------------------------------------
# Database (SQLite for local dev)
# --------------------------------------------------
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}


DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///db.sqlite3",
        conn_max_age=600,
        ssl_require=True
    )
}

# --------------------------------------------------
# Password validation (disabled for dev)
# --------------------------------------------------
AUTH_PASSWORD_VALIDATORS = []

# --------------------------------------------------
# Internationalization
# --------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# Static files
# --------------------------------------------------
STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / "staticfiles"

# --------------------------------------------------
# Default primary key field
# --------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------
# Auth redirects
# --------------------------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/student/dashboard/'
LOGOUT_REDIRECT_URL = '/'

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CSRF_TRUSTED_ORIGINS = ["https://*.up.railway.app"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")