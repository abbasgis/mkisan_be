"""
Django settings for mkisan_be project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
from datetime import timedelta
from pathlib import Path

from api.local_settings import API_APPS
# if os.name == 'nt':
#     import platform
#     OSGEO4W = r"C:\OSGeo4W"
#     if '64' in platform.architecture()[0]:
#         OSGEO4W += "64"
#     assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
#     os.environ['OSGEO4W_ROOT'] = OSGEO4W
#     os.environ['GDAL_DATA'] = OSGEO4W + r"\share\gdal"
#     os.environ['PROJ_LIB'] = OSGEO4W + r"\share\proj"
#     os.environ['PATH'] = OSGEO4W + r"\bin;" + os.environ['PATH']



# GEOS_LIBRARY_PATH = r'C:\OSGeo4W64\bin\geos_c.dll'
# GDAL_LIBRARY_PATH = r'E:\PycharmProjects\mkisan_be\venv\Lib\site-packages\osgeo\gdal304'
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static_root')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
COG_DIR = os.path.join(MEDIA_ROOT, 'cog')
UPLOADED_FILE_ROOT = os.path.join(MEDIA_ROOT, 'uploaded_files')
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-3kte3ft8o%fr_-f=ltss#76q@=typz1h-u=jfuc^1&@@@*447u'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
SITE_ID = 1
INSTALLED_APPS = [
                     'django.contrib.admin',
                     'django.contrib.auth',
                     'django.contrib.contenttypes',
                     'django.contrib.sessions',
                     'django.contrib.messages',
                     'django.contrib.staticfiles',
                     'django.contrib.gis',
                     'django.contrib.sites'
                 ] + API_APPS + [
                     'mkisan_be',
                     'map_viewer'
                 ]
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": "BOW2JOVIaI4JggR7wkrelSdACwNOAdMPCTkINXK8fEoFaXnbojvBj29FLHRwoiAS-WlYsf1stNIrU5vrripZPL4",
    "VAPID_PRIVATE_KEY": "OBpFv5XCDyCx8Vp4SSpWliXc46Nd2y7hcmiNRuvpBdU",
    "VAPID_ADMIN_EMAIL": "abbasgis@gmail.com"
}
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.logger.middleware.RequestInfo.CurrentUserMiddleware'
]

ROOT_URLCONF = 'mkisan_be.urls'

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

WSGI_APPLICATION = 'mkisan_be.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
DATABASE_ROUTERS = ['api.routers.MultiDatabaseRouter']
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'mera_kisan',
        'USER': 'postgres',  # Not used with sqlite3.
        # 'PASSWORD': '123',  # Not used with sqlite3.
        # 'HOST': 'localhost',  # Set to empty string for localhost. Not used with sqlite3.
        'PASSWORD': 'pg123@meraKisan',  # Not used with sqlite3.
        'HOST': '65.1.240.23',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432'
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    # "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated", ],
    # "rest_framework.permissions.IsAuthenticated", ],  # AllowAny
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        'rest_framework.parsers.MultiPartParser'],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        'rest_framework.authentication.BasicAuthentication',
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication"
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    'EXCEPTION_HANDLER': 'api.logger.middleware.LogHandler.api_exception_handler',

}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
}

CORS_ORIGIN_ALLOW_ALL = True
# CSRF_TRUSTED_ORIGINS = ['http://localhost:5000']
# CORS_ALLOW_HEADERS = list(default_headers) + [
#     'X-SESSION-KEY', 'HTTP-X-REQUESTED-WITH ', 'X-LOGIN-REQUIRED'
# ]
