from django.core import urlresolvers
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

    def get_success_url(self):
        return urlresolvers.reverse('feedback_complete')
