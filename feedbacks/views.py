from django.core import urlresolvers
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView
from django.views.generic.base import TemplateView

from .forms import FeedbackForm
from .models import Feedback


class FeedbackComplete(TemplateView):
    template_name = 'feedbacks/feedback_complete.html'


class FeedbackCreate(CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = 'feedbacks/feedback_form.html'

    # Since this view can get POSTed by any page, serving CSRF tokens on those
    # pages means the whole site gets uncacheable. So we disable CSRF for this
    # view. This means an outsider can spoof feedback, but that's probably OK -
    # the ramifications of such an "attack" are minor at most.
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_success_url(self):
        return urlresolvers.reverse('feedback_complete')
