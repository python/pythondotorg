from braces.views import LoginRequiredMixin as BracesLoginRequiredMixin
from django.contrib import messages


class LoginRequiredMixin(BracesLoginRequiredMixin):
    login_message = None

    def no_permissions_fail(self, request=None):
        if self.login_message is not None:
            messages.info(self.request, self.login_message)
        return super().no_permissions_fail(request=request)
