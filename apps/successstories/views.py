"""Views for listing, creating, and displaying success stories."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView
from honeypot.decorators import check_honeypot

from apps.successstories.forms import StoryForm
from apps.successstories.models import Story, StoryCategory


class ContextMixin:
    """Mixin that adds all story categories to the template context."""

    def get_context_data(self, **kwargs):
        """Add the full list of story categories to the context."""
        context = super().get_context_data(**kwargs)
        context["category_list"] = StoryCategory.objects.all()
        return context


class StoryCreate(LoginRequiredMixin, ContextMixin, CreateView):
    """View for authenticated users to submit a new success story."""

    model = Story
    form_class = StoryForm
    template_name = "successstories/story_form.html"
    success_message = (
        "Your success story submission has been recorded. It will be reviewed by the PSF staff and published."
    )

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        """Dispatch with honeypot spam protection."""
        return super().dispatch(*args, **kwargs)

    def get_success_url(self):
        """Return the URL to redirect to after successful submission."""
        return reverse("success_story_create")

    def form_valid(self, form):
        """Set the submitting user and display a success message on save."""
        obj = form.save(commit=False)
        obj.submitted_by = self.request.user
        messages.add_message(self.request, messages.SUCCESS, self.success_message)
        return super().form_valid(form)


class StoryDetail(ContextMixin, DetailView):
    """Detail view for a single success story."""

    template_name = "successstories/story_detail.html"
    context_object_name = "story"

    def get_queryset(self):
        """Return all stories for staff, published stories for everyone else."""
        if self.request.user.is_staff:
            return Story.objects.select_related()
        return Story.objects.select_related().published()


class StoryList(ListView):
    """List view showing the most recent published success stories."""

    template_name = "successstories/story_list.html"
    context_object_name = "stories"

    def get_queryset(self):
        """Return the latest published stories with related objects."""
        return Story.objects.select_related().latest()


class StoryListCategory(ContextMixin, DetailView):
    """Detail view for a story category, showing its associated stories."""

    model = StoryCategory
