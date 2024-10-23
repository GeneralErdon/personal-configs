"""
                   ____                 ____       _   _   _                 
                  / ___|___  _ __ ___  / ___|  ___| |_| |_(_)_ __   __ _ ___ 
                 | |   / _ \| '__/ _ \ \___ \ / _ \ __| __| | '_ \ / _` / __|
                 | |__| (_) | | |  __/  ___) |  __/ |_| |_| | | | | (_| \__ \
                  \____\___/|_|  \___| |____/ \___|\__|\__|_|_| |_|\__, |___/
                                                                   |___/     

This file contains the base and default configuration for the Django project.

Here, fundamental settings that are common to all environments are defined,
including:

- Database configuration
- Installed applications
- Middleware
- Internationalization settings
- Static and media files configuration
- Basic security settings
- And other essential Django settings

These settings provide a solid foundation for the project, which can then be
extended or modified in specific configuration files for different environments
(development, production, etc.).

Remember to review and adjust these settings according to the specific needs of your project.
"""
from environ import Env
from pathlib import Path
from core.database import get_db_config
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = Env()
env.read_env(BASE_DIR / ".env")


# ============================
#           SECRET KEY AND DEBUG
# ============================

SECRET_KEY = env.str("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", True)


# ============================
#           ALLOWED HOSTS AND CORS
# ============================

ALLOWED_HOSTS = [
    "*",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    *[f"http://{x}:5173" for x in env.list("DJANGO_DEVELOPING_CORS_ALLOWED")]
]

CORS_ORIGIN_WHITELIST = CORS_ALLOWED_ORIGINS


# ============================
#           APPLICATIONS
# ============================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    #"daphne",
    "rest_framework",
    "rest_framework_simplejwt",
    # 'rest_framework_simplejwt.token_blacklist',
    "corsheaders",
    "drf_yasg",
    "debug_toolbar",
    "channels",
    "channels_redis",
    "phonenumber_field",
    "unfold",
]

MY_APPS = [
    "core",
    "apps.base",
    "apps.users",
    "apps.human_resources.employees",
    "apps.human_resources.vacation",
    "apps.human_resources.payment",
    "apps.human_resources.company",
    "apps.notifications",
]

INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + MY_APPS


# ============================
#           MIDDLEWARE
# ============================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    "django.middleware.locale.LocaleMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ============================
#           ROOT URLCONF
# ============================

ROOT_URLCONF = 'core.urls'


# ============================
#           TEMPLATES
# ============================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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


# ============================
#           WSGI AND ASGI
# ============================

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = "core.asgi.application"


# ============================
#            DATABASE
# ============================

# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        **get_db_config(env.str("DB_ENGINE","sqlite"), BASE_DIR / "sqlite"),
    },
}


# ============================
#       PASSWORD VALIDATION
# ============================

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

AUTH_USER_MODEL = 'users.User'

# ============================
#       INTERNATIONALIZATION
# ============================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
]
LOCALE_PATHS = [
    BASE_DIR / "django_locale",
]

# ============================
#       STATIC FILES
# ============================

STATIC_URL = 'static/'
MEDIA_URL = "media/"
STATICFILES_DIRS = [
    BASE_DIR / "django_staticfiles",
]

STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media_root"

# ============================
#       DEFAULT PRIMARY KEY FIELD
# ============================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================
#       LOGGING CONFIGURATION
# ============================



AUTHENTICATION_BACKENDS = [
    'apps.base.oauth.authentication.AzureAdminAuthentication',
    # 'django.contrib.auth.backends.ModelBackend',  # Mantén este como respaldo
]

if not DEBUG:
    ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
    CSRF_TRUSTED_ORIGINS = [f"https://{x}" for x in env.list("DJANGO_ALLOWED_HOSTS")]
    CORS_ALLOWED_ORIGINS = [f"http://{x}" for x in env.list("DJANGO_PRODUCTION_CORS_ALLOWED")]
    CORS_ORIGIN_WHITELIST = CORS_ALLOWED_ORIGINS
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'file': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': BASE_DIR / 'logs' / 'django_errors.log',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }

    
    

