import os

from django.conf import settings

FAKE_PEP_REPO = os.path.join(settings.BASE, 'peps/tests/peps/')
FAKE_PEP_ARTIFACT = os.path.join(settings.BASE, 'peps/tests/peps.tar.gz')
