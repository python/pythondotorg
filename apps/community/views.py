"""Views for listing and displaying community posts."""

from django.views.generic import DetailView, ListView

from apps.community.models import Post


class PostList(ListView):
    """Paginated list view of community posts."""

    model = Post
    paginate_by = 25

    def get_queryset(self):
        """Only return public posts."""
        return Post.objects.public()


class PostDetail(DetailView):
    """Detail view for a single community post."""

    model = Post

    def get_queryset(self):
        """Only return public posts."""
        return Post.objects.public()
