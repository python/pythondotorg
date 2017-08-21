from django.core import serializers
from django.core.management import BaseCommand

from pages.models import Page


class Command(BaeeCommand):
    """
    Dump PEP related Pages as indented JSON
    """
    help = "Dump PEP related Pages as indented JSON"

    def handle(self, **options):
        qs = Page.objects.filter(path__startswith='peps/')

        serializers.serialize(
            format='json',
            queryset=qs,
            indent=4,
            stream=self.stdout,
        )
