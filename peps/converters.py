import re
import os

from bs4 import BeautifulSoup

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from pages.models import Page


def check_paths():
    """ Checks to ensure our PEP_REPO_PATH is setup correctly """
    if not hasattr(settings, 'PEP_REPO_PATH'):
        raise ImproperlyConfigured("No PEP_REPO_PATH in settings")

    if not os.path.exists(settings.PEP_REPO_PATH):
        raise ImproperlyConfigured("PEP_REPO_PATH in settings does not exist")


def convert_pep0():
    """
    Take existing generated pep-0000.html and convert to something suitable
    for a Python.org Page returns the core body HTML necessary only
    """
    check_paths()

    pep0_path = os.path.join(settings.PEP_REPO_PATH, 'pep-0000.html')
    pep0_content = open(pep0_path).read()

    soup = BeautifulSoup(pep0_content)

    body_children = list(soup.body.children)

    # Grab header and PEP body
    header = body_children[3]
    pep_content = body_children[7]

    # Fix PEP links
    body_links = pep_content.find_all("a")

    pep_href_re = re.compile(r'pep-(\d+)\.html')

    for b in body_links:
        m = pep_href_re.search(b.attrs['href'])

        # Skip anything not matching 'pep-XXXX.html'
        if not m:
            continue

        b.attrs['href'] = '/dev/peps/pep-{}/'.format(m.group(1))

    return ''.join([header.prettify(), pep_content.prettify()])


def get_pep0_page(commit=True):
    """
    Using convert_pep0 above, create a CMS ready pep0 page and return it
    """
    pep0_content = convert_pep0()
    pep0_page, _ = Page.objects.get_or_create(path='dev/peps/')
    pep0_page.content = pep0_content
    pep0_page.content_markup_type = 'html'
    pep0_page.title = "PEP 0 -- Index of Python Enhancement Proposals (PEPs)"

    if commit:
        pep0_page.save()

    return pep0_page


def convert_pep_page(pep_number, content):
    """
    Handle different formats that pep2html.py outputs
    """
    check_paths()
    data = {
        'title': None,
    }

    if '<html>' in content:
        soup = BeautifulSoup(content)
        data['title'] = soup.title.text

        header = soup.body.find('div', class_="header")
        data['header'] = header.prettify()

        main_content = soup.body.find('div', class_="content")

        data['main_content'] = main_content.prettify()
        data['content'] = ''.join([
            data['header'],
            data['main_content']
        ])

    else:
        soup = BeautifulSoup(content)

        # Attempt to find title in header table
        header_rows = soup.find_all('th', class_="field-name")
        for t in header_rows:
            if t.text == 'Version:' and t.next_sibling.text == '$Revision$':
                t.next_sibling.string = ''
            if t.text == 'Last-Modified:' and t.next_sibling.text == '$Date$':
                t.next_sibling.string = ''
            if t.text == 'Title:':
                data['title'] = t.next_sibling.text
            if t.text == 'Content-Type:':
                t.parent.extract()

        if not data['title']:
            data['title'] = "PEP {}".format(pep_number)

        data['content'] = soup.prettify()

    return data


def get_pep_page(pep_number, commit=True):
    """
    Given a pep_number retrieve original PEP source text, rst, or html.
    Get or create the associated Page and return it
    """
    pep_path = os.path.join(settings.PEP_REPO_PATH, 'pep-{}.html'.format(pep_number))
    if not os.path.exists(pep_path):
        print("PEP Path '{}' does not exist, skipping".format(pep_path))

    pep_content = convert_pep_page(pep_number, open(pep_path).read())

    pep_url = 'dev/peps/pep-{}/'.format(pep_number)
    pep_page, _ = Page.objects.get_or_create(path=pep_url)

    pep_page.title = pep_content['title']
    pep_page.content = pep_content['content']
    pep_page.content_markup_type = 'html'

    if commit:
        pep_page.save()

    return pep_page
