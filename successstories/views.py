from django.views.generic import CreateView, DetailView, ListView

from .forms import StoryForm
from .models import Story, StoryCategory


class StoryCreate(CreateView):
    model = Story
    form_class = StoryForm
    template_name = 'successstories/story_form.html'

    def get_success_url(self):
        return self.object.get_absolute_url()


class StoryDetail(DetailView):
    model = Story
    template_name = 'successstories/story_detail.html'
    context_object_name = 'story'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category_list'] = StoryCategory.objects.all()
        return ctx


class StoryList(ListView):
    model = Story
    template_name = 'successstories/story_list.html'
    context_object_name = 'stories'

    def get_queryset(self):
        return Story.objects.select_related().published()


class StoryListCategory(DetailView):
    model = StoryCategory
