from django.core import serializers
from django.core.management.base import NoArgsCommand

from pages.models import Page


class Command(NoArgsCommand):
    """
    Dump PEP related Pages as indented JSON
    """
    help = "Dump PEP related Pages as indented JSON"

    def handle_noargs(self, **options):
        qs = Page.objects.filter(path__startswith='peps/')

        serializers.serialize(
            format='json',
            queryset=qs,
            indent=4,
            stream=self.stdout,
        )
