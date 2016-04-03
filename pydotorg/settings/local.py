from .base import *

DEBUG = TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']

# Set the path to the location of the content files for python.org
# For example,
# PYTHON_ORG_CONTENT_SVN_PATH = '/Users/flavio/working_copies/beta.python.org/build/data'
PYTHON_ORG_CONTENT_SVN_PATH = ''

DATABASES = {
    'default': dj_database_url.config(default='postgres:///pythondotorg')
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Set the path to where the PEP repo's HTML source files are located
# For example, PEP_REPO_PATH = '/Users/frank/work/src/pythondotorg/tmp/peps'
PEP_REPO_PATH = ''

# Use Dummy SASS compiler to avoid performance issues and remove the need to
# have a sass compiler installed at all during local development if you aren't
# adjusting the CSS at all.  Comment this out or adjust it to suit your local
# environment needs if you are working with the CSS.
PIPELINE_COMPILERS = (
   'pydotorg.compilers.DummySASSCompiler',
)

INSTALLED_APPS += [
    'debug_toolbar',
]
