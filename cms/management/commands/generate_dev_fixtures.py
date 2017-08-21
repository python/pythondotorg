import gzip
import json
import io

from django.core.management import BaseCommand, call_command

from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    """
    Generate fixtures necessary for local development of production database.

    NOTE: This should be run as a cron job on the production www.python.org
    infrastructure, it is not useful to run this in a local environment except
    for testing/debugging purposes of this command itself.
    """

    help = 'Generate development fixtures for local development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default='/tmp/dev-fixtures.json.gz',
            dest='outputfile',
            help='Specifies the output file location of the fixtures.',
        )

    def handle(self, **options):
        outputfile = options.get('outputfile')

        content = io.StringIO()
        call_command(
            "dumpdata",
            format='json',
            indent=4,
            exclude=[
                "tastypie",
                "sessions",
                "account.emailconfirmation",
            ],
            stdout=content,
        )

        content.seek(0)
        raw_json = content.getvalue()
        data = json.loads(raw_json)

        # Scrub User passwords for security
        for obj in data:
            if obj['model'] != "users.user":
                continue
            obj['fields']['password'] = make_password(None)

        with gzip.open(outputfile, 'wb') as out:
            out.write(bytes(json.dumps(data, indent=4), 'UTF-8'))


