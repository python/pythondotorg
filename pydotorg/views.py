from django.conf import settings
from django.views.generic.base import RedirectView, TemplateView

from codesamples.models import CodeSample
from downloads.models import Release


class IndexView(TemplateView):
    template_name = "python/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'code_samples': CodeSample.objects.published()[:5],
        })
        return context


class AuthenticatedView(TemplateView):
    template_name = "includes/authenticated.html"


class DocumentationIndexView(TemplateView):
    template_name = 'python/documentation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'latest_python2': Release.objects.latest_python2(),
            'latest_python3': Release.objects.latest_python3(),
        })
        return context


class MediaMigrationView(RedirectView):
    prefix = None
    permanent = True
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        image_path = kwargs['url']
        if self.prefix:
            image_path = '/'.join([self.prefix, image_path])
        return '/'.join([
            settings.AWS_S3_ENDPOINT_URL,
            settings.AWS_STORAGE_BUCKET_NAME,
            image_path,
        ])
