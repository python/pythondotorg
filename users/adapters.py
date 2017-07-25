import re

from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from allauth.account.adapter import DefaultAccountAdapter


class PythonDotOrgAdapter(DefaultAccountAdapter):

    # TODO: We may set ACCOUNT_USERNAME_VALIDATORS when we upgrade
    # django-allauth to 0.30.0 or a newer version.
    def clean_username(self, username):
        username = super().clean_username(username)
        # We need to use \A and \Z instead of ^ and $ respectively to
        # reject user names like 'username\n'. See #1045 for details.
        #
        # \A matches the actual start of string and \Z the actual end.
        # There can be only one of \A and \Z in a multiline string,
        # whereas $ may be matched in each line.
        if re.search(r'\A[\w.@+-]+\Z', username, flags=re.UNICODE) is None:
            raise ValidationError(
                _('Please don\'t use whitespace characters in username.'),
                code='invalid',
            )
        return username
