from django.contrib import messages
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView

from honeypot.decorators import check_honeypot

from .forms import StoryForm
from .models import Story, StoryCategory


class ContextMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_list'] = StoryCategory.objects.all()
        return context


class StoryCreate(ContextMixin, CreateView):
    model = Story
    form_class = StoryForm
    template_name = 'successstories/story_form.html'
    success_message = (
        'Your success story submission has been recorded. '
        'It will be reviewed by the PSF staff and published.'
    )

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('success_story_create')

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, self.success_message)
        return super().form_valid(form)

class StoryDetail(ContextMixin, DetailView):
    template_name = 'successstories/story_detail.html'
    context_object_name = 'story'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Story.objects.select_related()
        return Story.objects.select_related().published()


class StoryList(ListView):
    template_name = 'successstories/story_list.html'
    context_object_name = 'stories'

    def get_queryset(self):
        return Story.objects.select_related().latest()


class StoryListCategory(ContextMixin, DetailView):
    model = StoryCategory
