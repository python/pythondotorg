from django import forms

from .models import Page


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        fields = [
            'title',
            'path',
            'is_published',
            'content_markup_type',
            'content',
        ]


class PageMigrationForm(forms.Form):
    url = forms.CharField(help_text='Please reference a .ht file that will be imported. Example: https://svn.python.org/www/trunk/beta.python.org/build/data/content.ht')
