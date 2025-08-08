import json
import os
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.generic.base import RedirectView, TemplateView

from codesamples.models import CodeSample
from downloads.models import Release


def health(request):
    return HttpResponse('OK')


def serve_funding_json(request):
    """Serve the funding.json file from the static directory."""
    funding_json_path = os.path.join(settings.BASE, 'static', 'funding.json')
    try:
        with open(funding_json_path, 'r') as f:
            data = json.load(f)
        return JsonResponse(data)
    except FileNotFoundError:
        return JsonResponse({'error': 'funding.json not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in funding.json'}, status=500)


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
