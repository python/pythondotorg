import requests

from django.core.management import call_command
from django.core.management.base import NoArgsCommand
from django.conf import settings
from django.utils.six.moves import input


class Command(NoArgsCommand):
    """
    Download and load dev fixtures from www.python.org
    """
    help = "Download and load dev fixtures from python.org"

    def handle_noargs(self, **options):

        # Confirm the user wants to do this
        confirm = input("""You have requested to load the python.org development fixtures.
This will IRREVERSIBLY DESTROY all data currently in your local database.
Are you sure you want to do this?

    Type 'y' or 'yes' to continue, 'n' or 'no' to cancel:  """)

        if confirm in ('y', 'yes'):
        if confirm:
            print()
            print("Beginning download, note this can take a couple of minutes...")
            r = requests.get(settings.DEV_FIXTURE_URL, stream=True)

            if r.status_code != 200:
                print("Unable to download file: Received status code {}".format(r.status_code))

            with open('/tmp/dev-fixtures.json.gz', 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
                    f.flush()

            print("Download complete, loading fixtures")
            call_command('loaddata', '/tmp/dev-fixtures.json')
            print("END: Fixtures loaded")
