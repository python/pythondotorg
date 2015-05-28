import os
import dj_database_url

### Basic config

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEBUG = TEMPLATE_DEBUG = True
SITE_ID = 1
SECRET_KEY = 'its-a-secret-to-everybody'

# Until Sentry works on Py3, do errors the old-fashioned way.
ADMINS = []

# General project information
# These are available in the template as SITE_INFO.<title>
SITE_VARIABLES = {
    'site_name': 'Python.org',
    'site_descript': 'The official home of the Python Programming Language',
}

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

DATE_FORMAT = 'Y-m-d'

### Files (media and static)

MEDIA_ROOT = os.path.join(BASE, 'media')
MEDIA_URL = '/m/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE, 'static-root')
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE, 'static'),
]
STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'


### Authentication

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",

    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

LOGIN_REDIRECT_URL = 'home'
ACCOUNT_LOGOUT_REDIRECT_URL = 'home'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = True
SOCIALACCOUNT_QUERY_EMAIL = True

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
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
    "django.contrib.messages.context_processors.messages",
    "pydotorg.context_processors.site_info",
    "pydotorg.context_processors.url_name",
]

### URLs, WSGI, middleware, etc.

ROOT_URLCONF = 'pydotorg.urls'

MIDDLEWARE_CLASSES = (
    'pydotorg.middleware.AdminNoCaching',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'pages.middleware.PageFallbackMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
)

AUTH_USER_MODEL = 'users.User'

WSGI_APPLICATION = 'pydotorg.wsgi.application'

### Apps

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.redirects',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.comments',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'django_comments_xtd',
    'jsonfield',
    'pipeline',
    'sitetree',
    'timedelta',
    'imagekit',
    'haystack',
    'honeypot',

    'users',
    'boxes',
    'cms',
    'companies',
    'feedbacks',
    'community',
    'jobs',
    'pages',
    'sponsors',
    'successstories',
    'events',
    'minutes',
    'peps',
    'blogs',
    'downloads',
    'codesamples',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    #'allauth.socialaccount.providers.facebook',
    #'allauth.socialaccount.providers.github',
    #'allauth.socialaccount.providers.openid',
    #'allauth.socialaccount.providers.twitter',

    # Tastypie needs the `users` app to be already loaded.
    'tastypie',

]

# Fixtures

FIXTURE_DIRS = (
    os.path.join(BASE, 'fixtures'),
)

### Testing

SKIP_NETWORK_TESTS = True

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

### Development
DEV_FIXTURE_URL = 'https://www.python.org/m/fixtures/dev-fixtures.json.gz'

### Comments

COMMENTS_APP = 'django_comments_xtd'
COMMENTS_XTD_MAX_THREAD_LEVEL = 0
COMMENTS_XTD_FORM_CLASS = "jobs.forms.JobCommentForm"

### Honeypot
HONEYPOT_FIELD_NAME = 'email_body_text'
HONEYPOT_VALUE = 'write your message'

### Blog Feed URL
PYTHON_BLOG_FEED_URL = "http://feeds.feedburner.com/PythonInsider"
PYTHON_BLOG_URL = "http://blog.python.org"

### Registration mailing lists
MAILING_LIST_PSF_MEMBERS = "psf-members-announce-request@python.org"

### PEP Repo Location
PEP_REPO_PATH = ''

### Fastly ###
FASTLY_API_KEY = False  # Set to Fastly API key in production to allow pages to
                        # be purged on save

# Jobs
JOB_THRESHOLD_DAYS = 90
JOB_FROM_EMAIL = 'jobs@python.org'

### Pipeline

from .pipeline import (
    PIPELINE_CSS, PIPELINE_JS,
    PIPELINE_COMPILERS,
    PIPELINE_SASS_BINARY, PIPELINE_SASS_ARGUMENTS,
    PIPELINE_CSS_COMPRESSOR, PIPELINE_JS_COMPRESSOR,
)
