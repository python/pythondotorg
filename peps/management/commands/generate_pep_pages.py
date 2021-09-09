import re
import os

from contextlib import ExitStack
from tarfile import TarFile
from tempfile import TemporaryDirectory, TemporaryFile

import requests

from django.core.management import BaseCommand
from django.conf import settings

from dateutil.parser import parse as parsedate

from peps.converters import (
    get_pep0_page, get_pep_page, add_pep_image, get_peps_rss, get_peps_last_updated
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

        with ExitStack() as stack:
            if settings.PEP_REPO_PATH is not None:
                artifacts_path = settings.PEP_REPO_PATH
            else:
                verbose(f"== Fetching PEP artifact from {settings.PEP_ARTIFACT_URL}")
                temp_file = self.get_artifact_tarball(stack)
                if not temp_file:
                    verbose("== No update to artifacts, we're done here!")
                    return
                temp_dir = stack.enter_context(TemporaryDirectory())
                tar_ball = stack.enter_context(TarFile.open(fileobj=temp_file, mode='r:gz'))
                tar_ball.extractall(path=temp_dir, numeric_owner=False)

                artifacts_path = os.path.join(temp_dir, 'peps')

            verbose("Generating RSS Feed")
            peps_rss = get_peps_rss(artifacts_path)
            if not peps_rss:
                verbose("Could not find generated RSS feed. Skipping.")

            verbose("Generating PEP0 index page")
            pep0_page, _ = get_pep0_page(artifacts_path)
            if pep0_page is None:
                verbose("HTML version of PEP 0 cannot be generated.")
                return

            image_paths = set()

            # Find pep pages
            for f in os.listdir(artifacts_path):

                if self.is_image(f):
                    verbose(f"- Deferring import of image '{f}'")
                    image_paths.add(f)
                    continue

                # Skip files we aren't looking for
                if not self.is_pep_page(f):
                    verbose(f"- Skipping non-PEP file '{f}'")
                    continue

                if 'pep-0000.html' in f:
                    verbose("- Skipping duplicate PEP0 index")
                    continue

                verbose(f"Generating PEP Page from '{f}'")
                pep_match = pep_number_re.match(f)
                if pep_match:
                    pep_number = pep_match.groups(1)[0]
                    p = get_pep_page(artifacts_path, pep_number)
                    if p is None:
                        verbose(
                            "- HTML version PEP {!r} cannot be generated.".format(
                                pep_number
                            )
                        )
                    verbose(f"====== Title: '{p.title}'")
                else:
                    verbose(f"- Skipping invalid '{f}'")

            # Find pep images. This needs to happen afterwards, because we need
            for img in image_paths:
                pep_match = pep_number_re.match(img)
                if pep_match:
                    pep_number = pep_match.groups(1)[0]
                    verbose("Generating image for PEP {} at '{}'".format(
                        pep_number, img))
                    add_pep_image(artifacts_path, pep_number, img)
                else:
                    verbose(f"- Skipping non-PEP related image '{img}'")

        verbose("== Finished")

    def get_artifact_tarball(self, stack):
        artifact_url = settings.PEP_ARTIFACT_URL
        if not artifact_url.startswith(('http://', 'https://')):
            return stack.enter_context(open(artifact_url, 'rb'))

        peps_last_updated = get_peps_last_updated()
        with requests.get(artifact_url, stream=True) as r:
            artifact_last_modified = parsedate(r.headers['last-modified'])
            if peps_last_updated > artifact_last_modified:
                return

            temp_file = stack.enter_context(TemporaryFile())
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)

        temp_file.seek(0)
        return temp_file
