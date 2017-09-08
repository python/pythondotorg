from django.views.generic.base import TemplateView

from codesamples.models import CodeSample
from downloads.models import Release

from .mixins import JSONResponseMixin


class IndexView(TemplateView):
    template_name = "python/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'code_samples': CodeSample.objects.published()[:5],
        })
        return context


class DocumentationIndexView(TemplateView):
    template_name = 'python/documentation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'latest_python2': Release.objects.latest_python2(),
            'latest_python3': Release.objects.latest_python3(),
        })
        return context


class RetiredAPIView(JSONResponseMixin, TemplateView):

    def render_to_response(self, context, **response_kwargs):
        response_kwargs['status'] = 410
        return self.render_to_json_response(context, **response_kwargs)

    def get_data(self, context):
        return {
            'message': (
                'This API is deprecated. Please get your new API token and '
                'use the \'/api/v2/\' base URL with the same endpoints.'
            )
        }

    post = put = patch = delete = TemplateView.get
