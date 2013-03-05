import os
import dj_database_url

### Basic config

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEBUG = TEMPLATE_DEBUG = True
SITE_ID = 1
SECRET_KEY = 'hu9h&&%j*tcj2o9!k2w%ao=fcw&$0z$)la$&8vl+s$4y%r946h'

### Databases

DATABASES = {
    'default': dj_database_url.config(default='postgres:///python.org')
}

### Locale settings

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True
USE_TZ = True

### Files (media and static)

MEDIA_ROOT = os.path.join(BASE, 'media')
MEDIA_URL = '/m/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE, 'static-root')
STATIC_URL = '/static/'

STATICFILES_DIRS = (os.path.join(BASE, 'static'),)
STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'

### Templates

TEMPLATE_DIRS = [
    os.path.join(BASE, 'templates')
]

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
]

### URLs, WSGI, middleware, etc.

ROOT_URLCONF = 'pydotorg.urls'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

WSGI_APPLICATION = 'pydotorg.wsgi.application'

### Apps

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'pipeline',
    'sitetree',
    'south',

    'boxes',
    'cms',
    'companies',
    'jobs',
    'pages',
    'sponsors',
    'successstories',
)

### Testing

TEST_RUNNER = 'discover_runner.DiscoverRunner'
TEST_DISCOVER_TOP_LEVEL = BASE
### Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

from .pipeline import (
    PIPELINE_CSS, PIPELINE_JS,
    PIPELINE_COMPILERS,
    PIPELINE_SASS_BINARY, PIPELINE_SASS_ARGUMENTS,
    PIPELINE_CSS_COMPRESSOR, PIPELINE_JS_COMPRESSOR,
    PIPELINE_YUI_BINARY,
)
