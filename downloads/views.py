from django.views.generic import DetailView, ListView, TemplateView

from .models import OS, Release


class DownloadHome(TemplateView):
    template_name = 'python/download.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'latest_python2': Release.objects.python2().latest(),
            'latest_python3': Release.objects.python3().latest(),
            'releases': Release.objects.downloads(),
        })

        return context


class DownloadOSList(ListView):

    def get_queryset(self):
        return OS.objects.filter(slug=self.kwargs['os_slug'])


class DownloadReleaseDetail(DetailView):
    model = Release

    def get_queryset(self):
        return super().get_queryset().filter(slug=self.kwargs['release_slug'])
