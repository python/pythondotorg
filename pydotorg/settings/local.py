from .base import *

DEBUG = True
TEMPLATE_DEBUG = True
PYTHON_ORG_CONTENT_SVN_PATH='/Users/flavio/working_copies/beta.python.org/build/data'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

PEP_REPO_PATH = '/Users/frank/work/src/pythondotorg/tmp/peps'

# Use Dummy SASS compiler to avoid performance issues and remove the need to
# have a sass compiler installed at all during local development if you aren't
# adjusting the CSS at all.  Comment this out or adjust it to suit your local
# environment needs if you are working with the CSS.
PIPELINE_COMPILERS = (
   'pydotorg.compilers.DummySASSCompiler',
)
