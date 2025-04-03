"""
Django settings for geotune_project project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-58=76dj76m5un4z=hoag1mg0d#7$3+wqpkk&8b@z@*0!%#fiph'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'geotune',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'geotune_project.urls'

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
                'geotune.context_processors.verbindungsanfragen',
            ],
        },
    },
]

WSGI_APPLICATION = 'geotune_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ['username', 'email', 'first_name', 'last_name'],
            'max_similarity': 0.7,
        },
        'MESSAGE': 'Das Passwort ist zu ähnlich zu deinem Benutzernamen oder anderen persönlichen Informationen.',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        },
        'MESSAGE': 'Das Passwort muss mindestens 8 Zeichen lang sein.',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        'MESSAGE': 'Das Passwort ist zu einfach und zu häufig verwendet.',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        'MESSAGE': 'Das Passwort darf nicht nur aus Zahlen bestehen.',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_TZ = True

# Benutzerdefinierte Validierungsnachrichten
# FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

# Deutsche Validierungsnachrichten
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Definiere das benutzerdefinierte Nutzermodell
AUTH_USER_MODEL = 'geotune.Nutzer'

# Statische Dateien und Medien-Einstellungen
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Crispy-Forms-Einstellungen
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Login-Redirects
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Email-Konfiguration (für Entwicklung - Console-Backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Im Produktivbetrieb könnte hier ein SMTP-Backend konfiguriert werden:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'user@example.com'
# EMAIL_HOST_PASSWORD = 'password'
# EMAIL_USE_TLS = True
# DEFAULT_FROM_EMAIL = 'GeoTune <noreply@geotune.example.com>'