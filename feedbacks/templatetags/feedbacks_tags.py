from django import template

from ..forms import FeedbackForm, FeedbackMiniForm

register = template.Library()


@register.inclusion_tag('feedbacks/includes/feedback_form.html')
def get_feedback_form(*args, **kwargs):
    return {
        'form': FeedbackForm()
    }


@register.inclusion_tag('feedbacks/includes/feedback_mini_form.html')
def get_feedback_mini_form(*args, **kwargs):
    return {
        'form': FeedbackMiniForm()
    }
