import re
import os

from django.core.management import BaseCommand
from django.conf import settings

from peps.converters import (
    get_pep0_page, get_pep_page, add_pep_image, get_peps_rss
)

pep_number_re = re.compile(r'pep-(\d+)')


class Command(BaseCommand):
    """
    Generate CMS Pages from flat file PEP data.

    Run this command AFTER normal RST -> HTML PEP transformation from the PEP
    repository has happened. This works on the HTML files created during that
    process.

    For verbose output run this with:

        ./manage.py generate_pep_pages --verbosity=2
    """
    help = "Generate PEP Page objects from rendered HTML"

    def is_pep_page(self, path):
        return path.startswith('pep-') and path.endswith('.html')

    def is_image(self, path):
        # All images are pngs
        return path.endswith('.png')

    def handle(self, **options):
        verbosity = int(options['verbosity'])

        def verbose(msg):
            """ Output wrapper """
            if verbosity > 1:
                print(msg)

        verbose("== Starting PEP page generation")

        verbose("Generating RSS Feed")
        peps_rss = get_peps_rss()
        if not peps_rss:
            verbose("Could not find generated RSS feed. Skipping.")

        verbose("Generating PEP0 index page")
        pep0_page, _ = get_pep0_page()
        if pep0_page is None:
            verbose("HTML version of PEP 0 cannot be generated.")
            return

        image_paths = set()

        # Find pep pages
        for f in os.listdir(settings.PEP_REPO_PATH):

            if self.is_image(f):
                verbose("- Deferring import of image '{}'".format(f))
                image_paths.add(f)
                continue

            # Skip files we aren't looking for
            if not self.is_pep_page(f):
                verbose("- Skipping non-PEP file '{}'".format(f))
                continue

            if 'pep-0000.html' in f:
                verbose("- Skipping duplicate PEP0 index")
                continue

            verbose("Generating PEP Page from '{}'".format(f))
            pep_match = pep_number_re.match(f)
            if pep_match:
                pep_number = pep_match.groups(1)[0]
                p = get_pep_page(pep_number)
                if p is None:
                    verbose(
                        "- HTML version PEP {!r} cannot be generated.".format(
                            pep_number
                        )
                    )
                verbose("====== Title: '{}'".format(p.title))
            else:
                verbose("- Skipping invalid '{}'".format(f))

        # Find pep images. This needs to happen afterwards, because we need
        for img in image_paths:
            pep_match = pep_number_re.match(img)
            if pep_match:
                pep_number = pep_match.groups(1)[0]
                verbose("Generating image for PEP {} at '{}'".format(
                    pep_number, img))
                add_pep_image(pep_number, img)
            else:
                verbose("- Skipping non-PEP related image '{}'".format(img))

        verbose("== Finished")
