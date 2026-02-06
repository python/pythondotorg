"""Views for listing and displaying community posts."""

from django.views.generic import DetailView, ListView

from community.models import Post


class PostList(ListView):
    """Paginated list view of community posts."""

    model = Post
    paginate_by = 25


class PostDetail(DetailView):
    """Detail view for a single community post."""

    model = Post
