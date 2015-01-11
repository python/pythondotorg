from django.shortcuts import render


def custom_404(request, template_name='404.html'):
    """ Custom 404 handler to only cache 404s for 5 mintues """

    response = render(request, template_name)
    response['Cache-Control'] = 'max-age=300'
    response.status_code = 404

    return response