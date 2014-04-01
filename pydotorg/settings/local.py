from .base import *

DEBUG = True
TEMPLATE_DEBUG = True

# If you have an existing SVN checkout locally, put the path below.
#PYTHON_ORG_CONTENT_SVN_PATH=''

PYTHON_ORG_CONTENT_SVN_URL='https://svn.python.org/www/trunk/beta.python.org'

# Local path where the SVN checkout will be stored. Defaults to '/tmp'.
#SVN_CHECKOUT_PATH=''

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}
