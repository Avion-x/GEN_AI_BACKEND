"""
Django settings for user project.

Generated by 'django-admin startproject' using Django 5.0.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-6tuli!ti5-7370+$j5!$!1+z++l3785o((n!5xgxdd%=mgaxl@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = '*'

CORS_ALLOW_ALL_HEADERS = '*'

# Application definition

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'rest_framework.authtoken',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'user',
    'product',
]

MIDDLEWARE = [
    # 'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'user.middleware.request_tracking_middleware.RequestIDMiddleware',
]

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:4200",
# ]



# Disable CSRF protection
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = False  # Set to True if using HTTPS, False for development without HTTPS

ROOT_URLCONF = 'user.urls'

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

WSGI_APPLICATION = 'user.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'GEN_AI',
        'USER': 'admin',
        'PASSWORD': '-Mj8[q{!6gWF%th~l#|Hrlyd0S-y',
        'HOST': 'gen-ai.c54r5svdjqsu.us-west-2.rds.amazonaws.com',  # This is the endpoint of your RDS instance
        'PORT': '3306',  # Default MySQL port
        'OPTIONS': {
            # 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    },
    # 'default': {
    # 'ENGINE': 'django.db.backends.mysql',
    # 'NAME': 'GenAI',
    # 'USER': 'Admin',
    # 'PASSWORD': 'L4e1-#5L6zT)Nc',
    # 'HOST': 'genai-database-dev-1.cluster-c54r5svdjqsu.us-west-2.rds.amazonaws.com',  # This is the endpoint of your RDS instance
    # 'PORT': '3306',  # Default MySQL port
    # 'OPTIONS': {
    #     # 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    #     },
    # }
}



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

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'user.User'


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],

    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication'
    ],
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': f'{BASE_DIR}/log/log_file.log',  # Provide the full path
        },
    },
    'root': {
        'handlers': ['file'], # 'console' add it if you want to see logs in console
        'level': 'NOTSET',  # Accept log messages of all levels, You can Adjust the logging level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    },
}