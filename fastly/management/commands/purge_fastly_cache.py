from django.core.management import BaseCommand

from fastly import register


class Command(BaseCommand):

    def handle(self, **options):
        for cmd in register:
            cmd()
        self.stdout.write(self.style.SUCCESS('DONE'))
