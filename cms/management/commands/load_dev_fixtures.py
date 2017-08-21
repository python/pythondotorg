import sys

import requests

from django.core.management import BaseCommand, call_command
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.six.moves import input


class Command(BaseCommand):
    """
    Download and load dev fixtures from www.python.org
    """
    help = "Download and load dev fixtures from python.org"

    def handle(self, **options):

        # Confirm the user wants to do this
        confirm = input("""You have requested to load the python.org development fixtures.
This will IRREVERSIBLY DESTROY all data currently in your local database.
Are you sure you want to do this?

    Type 'y' or 'yes' to continue, 'n' or 'no' to cancel:  """)

        if confirm in ('y', 'yes'):
            self.stdout.write("\nBeginning download, note this can take a couple of minutes...")
            r = requests.get(settings.DEV_FIXTURE_URL, stream=True)

            if r.status_code != 200:
                self.stderr.write("Unable to download file: Received status code {}".format(r.status_code))
                sys.exit(1)

            # Remove pesky objects that get in the way
            Permission.objects.all().delete()
            ContentType.objects.all().delete()

            with open('/tmp/dev-fixtures.json.gz', 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
                    f.flush()

            self.stdout.write("Download complete, loading fixtures")
            call_command('loaddata', '/tmp/dev-fixtures.json')
            self.stdout.write("END: Fixtures loaded")
