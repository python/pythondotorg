import re
import os

from django.core.management.base import NoArgsCommand
from django.conf import settings

from peps.converters import get_pep0_page, get_pep_page

pep_number_re = re.compile(r'pep-(\d+)\.html')


class Command(NoArgsCommand):
    """
    Generate CMS Pages from flat file PEP data.

    Run this command AFTER normal RST -> HTML PEP transformation from the PEP
    repository has happened. This works on the HTML files created during that
    process.

    For verbose output run this with:

        ./manage.py generate_pep_pages --verbosity=2
    """
    help = "Generate PEP Page objects from rendered HTML"

    def handle_noargs(self, **options):
        verbosity = int(options['verbosity'])

        def verbose(msg):
            """ Output wrapper """
            if verbosity > 1:
                print(msg)

        verbose("== Starting PEP page generation")

        verbose("Generating PEP0 index page")
        pep0_page = get_pep0_page()

        # Find pep pages
        for f in os.listdir(settings.PEP_REPO_PATH):

            # Skip files we aren't looking for
            if not f.startswith('pep-') or not f.endswith('.html'):
                verbose("- Skipping non-PEP file '{}'".format(f))
                continue

            verbose("Generating PEP Page from '{}'".format(f))
            pep_match = pep_number_re.match(f)
            if pep_match:
                pep_number = pep_match.groups(1)[0]
                p = get_pep_page(pep_number)
            else:
                verbose("- Skipping invalid {}'".format(f))

        verbose("== Finished")
