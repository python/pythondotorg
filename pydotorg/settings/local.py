from .base import *
import os

DEBUG = True

ALLOWED_HOSTS = ['*']
INTERNAL_IPS = ['127.0.0.1']

# Set the path to the location of the content files for python.org
# For example,
# PYTHON_ORG_CONTENT_SVN_PATH = '/Users/flavio/working_copies/beta.python.org/build/data'
PYTHON_ORG_CONTENT_SVN_PATH = ''

DATABASES = {
    'default': dj_database_url.config(default='postgres:///pythondotorg')
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch5_backend.Elasticsearch5SearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Set the local pep repository path to fetch PEPs from,
# or none to fallback to the tarball specified by PEP_ARTIFACT_URL.
PEP_REPO_PATH = os.environ.get('PEP_REPO_PATH', None)  # directory path or None

# Set the path to where to fetch PEP artifacts from.
# The value can be a local path or a remote URL.
# Ignored if PEP_REPO_PATH is set.
PEP_ARTIFACT_URL = os.path.join(BASE, 'peps/tests/peps.tar.gz')

# Use Dummy SASS compiler to avoid performance issues and remove the need to
# have a sass compiler installed at all during local development if you aren't
# adjusting the CSS at all.  Comment this out or adjust it to suit your local
# environment needs if you are working with the CSS.
# PIPELINE['COMPILERS'] = (
#    'pydotorg.compilers.DummySASSCompiler',
# )
# Pass '-XssNNNNNk' to 'java' if you get 'java.lang.StackOverflowError' with
# yui-compressor.
# PIPELINE['YUI_BINARY'] = '/usr/bin/java -Xss200048k -jar /usr/share/yui-compressor/yui-compressor.jar'

INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += (
    'rest_framework.renderers.BrowsableAPIRenderer',
)
