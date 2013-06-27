from django.views.generic import ListView, DetailView

from .models import Post


class PostList(ListView):
    model = Post
    paginate_by = 25


class PostDetail(DetailView):
    model = Post
