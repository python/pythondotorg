import requests

from django.contrib.formtools.wizard.views import SessionWizardView
from django.shortcuts import render_to_response
from django.views.generic import DetailView
from email.parser import Parser

from .models import Page


class PageView(DetailView):
    template_name = 'pages/default.html'
    template_name_field = 'template_name'
    context_object_name = 'page'

    # Use "path" as the lookup key, rather than the default "slug".
    slug_url_kwarg = 'path'
    slug_field = 'path'

    def get_queryset(self):
        # FIXME: show draft pages to... certain people... once we define who.
        return Page.objects.published()


class PageWizard(SessionWizardView):
    template_name = 'pages/page_form.html'

    def clean_filename(self, filename):
        filename = filename.replace('https://svn.python.org/www/trunk/beta.python.org/build/data/', '')
        filename = filename.replace('/content.ht', '')
        #filename = 'pages/{}'.format(filename)
        return filename.strip('/')

    def get_form_initial(self, step):
        kwargs = {}

        if step == '1':
            url = self.get_cleaned_data_for_step('0')['url']
            req = requests.get(url, verify=False).content.decode()

            headers = Parser().parsestr(req)
            content = '\n\n'.join(req.split('\n\n')[1:])

            kwargs.update({
                'title': headers['Title'],
                'path': self.clean_filename(url),
                'content': content,
            })

        return kwargs

    def get_form(self, step=None, data=None, files=None):
        form = super().get_form(step, data, files)
        if step == '1':
            form.creator = self.request.user
        return form

    #def process_step(self, form):
    #    return self.get_form_step_data(form)

    def done(self, form_list, **kwargs):
        return render_to_response('pages/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
        })
