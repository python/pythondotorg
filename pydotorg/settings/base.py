"""Base Django settings for the python.org project."""

from pathlib import Path

from decouple import config
from dj_database_url import parse as dj_database_url_parser
from django.contrib.messages import constants

from pydotorg.settings.pipeline import PIPELINE  # noqa: F401 - accessed by django-pipeline via settings

### Basic config

BASE = str(Path(__file__).resolve().parent.parent.parent)
DEBUG = True
SITE_ID = 1
SECRET_KEY = "its-a-secret-to-everybody"  # noqa: S105 - development-only default, overridden in production

# Until Sentry works on Py3, do errors the old-fashioned way.
ADMINS = []

# General project information
# These are available in the template as SITE_INFO.<title>
SITE_VARIABLES = {
    "site_name": "Python.org",
    "site_descript": "The official home of the Python Programming Language",
}

### Databases

DATABASES = {"default": config("DATABASE_URL", default="postgres:///python.org", cast=dj_database_url_parser)}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
"""The default primary key field type for Django models.

Required during the Django 2.2 -> 4.2 migration.
"""

# celery settings
_REDIS_URL = config("REDIS_URL", default="redis://redis:6379/0")

CELERY_BROKER_URL = _REDIS_URL
CELERY_RESULT_BACKEND = _REDIS_URL

CELERY_BEAT_SCHEDULE = {}

### Locale settings

TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en-us", "English"),
]
USE_I18N = True
USE_TZ = True

DATE_FORMAT = "Y-m-d"

# Media and static file configuration

MEDIA_ROOT = str(Path(BASE) / "media")
MEDIA_URL = "/media/"
MEDIAFILES_LOCATION = "media"

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
STATIC_ROOT = str(Path(BASE) / "static-root")
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    str(Path(BASE) / "static"),
]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "pipeline.storage.PipelineStorage",
    },
}
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.PipelineFinder",
)

### Authentication

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

### Allauth
LOGIN_REDIRECT_URL = "home"
ACCOUNT_LOGOUT_REDIRECT_URL = "home"
ACCOUNT_LOGIN_METHODS = {"email", "username"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# TODO: Enable enumeration prevention
ACCOUNT_PREVENT_ENUMERATION = False
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = True
SOCIALACCOUNT_QUERY_EMAIL = True
ACCOUNT_USERNAME_VALIDATORS = "apps.users.validators.username_validators"

### Templates

TEMPLATES_DIR = str(Path(BASE) / "templates")
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            TEMPLATES_DIR,
        ],
        "OPTIONS": {
            "loaders": [
                "apptemplates.Loader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "pydotorg.context_processors.site_info",
                "pydotorg.context_processors.url_name",
                "pydotorg.context_processors.get_host_with_scheme",
                "pydotorg.context_processors.blog_url",
                "pydotorg.context_processors.user_nav_bar_links",
            ],
        },
    },
]

FORM_RENDERER = "django.forms.renderers.DjangoTemplates"

### URLs, WSGI, middleware, etc.

ROOT_URLCONF = "pydotorg.urls"

# Note that we don't need to activate 'XFrameOptionsMiddleware' and
# 'SecurityMiddleware' because we set appropriate headers in python/psf-salt.
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "pydotorg.middleware.AdminNoCaching",
    "pydotorg.middleware.GlobalSurrogateKey",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.pages.middleware.PageFallbackMiddleware",
    "django.contrib.redirects.middleware.RedirectFallbackMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

AUTH_USER_MODEL = "users.User"

WSGI_APPLICATION = "pydotorg.wsgi.application"

### Apps

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.redirects",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "admin_interface",
    "colorfield",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django_celery_beat",
    "django_translation_aliases",
    "pipeline",
    "sitetree",
    "imagekit",
    "haystack",
    "honeypot",
    "waffle",
    "ordered_model",
    "widget_tweaks",
    "django_countries",
    "sorl.thumbnail",
    "pydotorg",
    "apps.banners",
    "apps.blogs",
    "apps.boxes",
    "apps.cms",
    "apps.codesamples",
    "apps.community",
    "apps.companies",
    "apps.downloads",
    "apps.events",
    "apps.jobs",
    "apps.mailing",
    "apps.minutes",
    "apps.nominations",
    "apps.pages",
    "apps.sponsors",
    "apps.successstories",
    "apps.users",
    "apps.work_groups",
    "allauth",
    "allauth.account",
    # Tastypie needs the `users` app to be already loaded.
    "tastypie",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "polymorphic",
    "django_extensions",
    "import_export",
]

# Fixtures

FIXTURE_DIRS = (str(Path(BASE) / "fixtures"),)

### Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

### Honeypot
HONEYPOT_FIELD_NAME = "email_body_text"
HONEYPOT_VALUE = "write your message"

### Blog Feed URL
PYTHON_BLOG_FEED_URL = "https://blog.python.org/feeds/posts/default?alt=rss"
PYTHON_BLOG_URL = "https://blog.python.org"

### Registration mailing lists
MAILING_LIST_PSF_MEMBERS = "psf-members-announce-request@python.org"

### Fastly ###
FASTLY_API_KEY = False  # Set to Fastly API key in production to allow pages to
# be purged on save
FASTLY_SERVICE_ID = config("FASTLY_SERVICE_ID", default=None)  # Required for surrogate key purging

# Jobs
JOB_THRESHOLD_DAYS = 90
JOB_FROM_EMAIL = "jobs@python.org"

# Events
EVENTS_TO_EMAIL = "events@python.org"

# Sponsors
SPONSORSHIP_NOTIFICATION_FROM_EMAIL = config("SPONSORSHIP_NOTIFICATION_FROM_EMAIL", default="sponsors@python.org")
SPONSORSHIP_NOTIFICATION_TO_EMAIL = config("SPONSORSHIP_NOTIFICATION_TO_EMAIL", default="psf-sponsors@python.org")
PYPI_SPONSORS_CSV = str(Path(BASE) / "data" / "pypi-sponsors.csv")

# Mail
DEFAULT_FROM_EMAIL = "noreply@python.org"

### Pipeline


### contrib.messages

MESSAGE_TAGS = {
    constants.INFO: "general",
}

### SecurityMiddleware

X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]

### django-rest-framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework.authentication.TokenAuthentication",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "URL_FIELD_NAME": "resource_uri",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "3000/day",
    },
    "NUM_PROXIES": 3,
}

### pydotorg.middleware.GlobalSurrogateKey

GLOBAL_SURROGATE_KEY = "pydotorg-app"

### PyCon Integration for Sponsor Voucher Codes
PYCON_API_KEY = config("PYCON_API_KEY", default="deadbeef-dead-beef-dead-beefdeadbeef")
PYCON_API_SECRET = config("PYCON_API_SECRET", default="deadbeef-dead-beef-dead-beefdeadbeef")
PYCON_API_HOST = config("PYCON_API_HOST", default="localhost:8000")
