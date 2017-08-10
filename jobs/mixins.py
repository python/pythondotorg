from braces.views import LoginRequiredMixin as BracesLoginRequiredMixin
from django.contrib import messages


class LoginRequiredMixin(BracesLoginRequiredMixin):
    redirect_unauthenticated_users = True

    login_message = None

    def dispatch(self, request, *args, **kwargs):
        if self.login_message is not None:
            messages.info(self.request, self.login_message)
        return super().dispatch(request, *args, **kwargs)
