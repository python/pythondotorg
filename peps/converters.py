import functools
import datetime
import re
import os

from bs4 import BeautifulSoup

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
from django.db.models import Max

from pages.models import Page, Image

PEP_TEMPLATE = 'pages/pep-page.html'
pep_url = lambda num: f'dev/peps/pep-{num}/'


def get_peps_last_updated():
    last_update = Page.objects.filter(
        path__startswith='dev/peps',
    ).aggregate(Max('updated')).get('updated__max')
    if last_update is None:
        return datetime.datetime(
            1970, 1, 1, tzinfo=datetime.timezone(
                datetime.timedelta(0)
            )
        )
    return last_update


def convert_pep0(artifact_path):
    """
    Take existing generated pep-0000.html and convert to something suitable
    for a Python.org Page returns the core body HTML necessary only
    """
    pep0_path = os.path.join(artifact_path, 'pep-0000.html')
    pep0_content = open(pep0_path).read()
    data = convert_pep_page(0, pep0_content)
    if data is None:
        return
    return data['content']


def get_pep0_page(artifact_path, commit=True):
    """
    Using convert_pep0 above, create a CMS ready pep0 page and return it

    pep0 is used as the directory index, but it's also an actual pep, so we
    return both Page objects.
    """
    pep0_content = convert_pep0(artifact_path)
    if pep0_content is None:
        return None, None
    pep0_page, _ = Page.objects.get_or_create(path='dev/peps/')
    pep0000_page, _ = Page.objects.get_or_create(path='dev/peps/pep-0000/')
    for page in [pep0_page, pep0000_page]:
        page.content = pep0_content
        page.content_markup_type = 'html'
        page.title = "PEP 0 -- Index of Python Enhancement Proposals (PEPs)"
        page.template_name = PEP_TEMPLATE

        if commit:
            page.save()

    return pep0_page, pep0000_page


def fix_headers(soup, data):
    """ Remove empty or unwanted headers and find our title """
    header_rows = soup.find_all('th')
    for t in header_rows:
        if 'Version:' in t.text:
            if t.next_sibling.text == '$Revision$':
                t.parent.extract()
            if t.next_sibling.text == '':
                t.parent.extract()
        if 'Last-Modified:' in t.text:
            if '$Date$'in t.next_sibling.text:
                t.parent.extract()
            if t.next_sibling.text == '':
                t.parent.extract()
        if t.text == 'Title:':
            data['title'] = t.next_sibling.text
        if t.text == 'Content-Type:':
            t.parent.extract()
        if 'Version:' in t.text and 'N/A' in t.next_sibling.text:
            t.parent.extract()

    return soup, data


def convert_pep_page(pep_number, content):
    """
    Handle different formats that pep2html.py outputs
    """
    data = {
        'title': None,
    }
    # Remove leading zeros from PEP number for display purposes
    pep_number_humanize = re.sub(r'^0+', '', str(pep_number))

    if '<html>' in content:
        soup = BeautifulSoup(content, 'lxml')
        data['title'] = soup.title.text

        if not re.search(r'PEP \d+', data['title']):
            data['title'] = 'PEP {} -- {}'.format(
                pep_number_humanize,
                soup.title.text,
            )

        header = soup.body.find('div', class_="header")
        header, data = fix_headers(header, data)
        data['header'] = str(header)

        main_content = soup.body.find('div', class_="content")

        data['main_content'] = str(main_content)
        data['content'] = ''.join([
            data['header'],
            data['main_content']
        ])

    else:
        soup = BeautifulSoup(content, 'lxml')

        soup, data = fix_headers(soup, data)
        if not data['title']:
            data['title'] = f"PEP {pep_number_humanize} -- "
        else:
            if not re.search(r'PEP \d+', data['title']):
                data['title'] = "PEP {} -- {}".format(
                    pep_number_humanize,
                    data['title'],
                )

        data['content'] = str(soup)

    # Fix PEP links
    pep_content = BeautifulSoup(data['content'], 'lxml')
    body_links = pep_content.find_all("a")

    pep_href_re = re.compile(r'pep-(\d+)\.html')

    for b in body_links:
        m = pep_href_re.search(b.attrs['href'])

        # Skip anything not matching 'pep-XXXX.html'
        if not m:
            continue

        b.attrs['href'] = f'/dev/peps/pep-{m.group(1)}/'

    # Return early if 'html' or 'body' return None.
    if pep_content.html is None or pep_content.body is None:
        return

    # Strip <html> and <body> tags.
    pep_content.html.unwrap()
    pep_content.body.unwrap()

    data['content'] = str(pep_content)
    return data


def get_pep_page(artifact_path, pep_number, commit=True):
    """
    Given a pep_number retrieve original PEP source text, rst, or html.
    Get or create the associated Page and return it
    """
    pep_path = os.path.join(artifact_path, f'pep-{pep_number}.html')
    if not os.path.exists(pep_path):
        print(f"PEP Path '{pep_path}' does not exist, skipping")
        return

    pep_content = convert_pep_page(pep_number, open(pep_path).read())
    if pep_content is None:
        return None
    pep_rst_source = os.path.join(
        artifact_path, f'pep-{pep_number}.rst',
    )
    pep_ext = '.rst' if os.path.exists(pep_rst_source) else '.txt'
    source_link = 'https://github.com/python/peps/blob/master/pep-{}{}'.format(
        pep_number, pep_ext)
    pep_content['content'] += """Source: <a href="{0}">{0}</a>""".format(source_link)

    pep_page, _ = Page.objects.get_or_create(path=pep_url(pep_number))

    pep_page.title = pep_content['title']

    pep_page.content = pep_content['content']
    pep_page.content_markup_type = 'html'
    pep_page.template_name = PEP_TEMPLATE

    if commit:
        pep_page.save()

    return pep_page


def add_pep_image(artifact_path, pep_number, path):
    image_path = os.path.join(artifact_path, path)
    if not os.path.exists(image_path):
        print(f"Image Path '{image_path}' does not exist, skipping")
        return

    try:
        page = Page.objects.get(path=pep_url(pep_number))
    except Page.DoesNotExist:
        print(f"Could not find backing PEP {pep_number}")
        return

    # Find existing images, we have to loop here as we can't use the ORM
    # to query against image__path
    existing_images = Image.objects.filter(page=page)

    FOUND = False
    for image in existing_images:
        if image.image.name.endswith(path):
            FOUND = True
            break

    if not FOUND:
        image = Image(page=page)

        with open(image_path, 'rb') as image_obj:
            image.image.save(path, File(image_obj))
        image.save()

    # Old images used to live alongside html, but now they're in different
    # places, so update the page accordingly.
    soup = BeautifulSoup(page.content.raw, 'lxml')
    for img_tag in soup.findAll('img'):
        if img_tag['src'] == path:
            img_tag['src'] = image.image.url

    page.content.raw = str(soup)
    page.save()

    return image


def get_peps_rss(artifact_path):
    rss_feed = os.path.join(artifact_path, 'peps.rss')
    if not os.path.exists(rss_feed):
        return

    page, _ = Page.objects.get_or_create(
        path="dev/peps/peps.rss",
        template_name="pages/raw.html",
    )

    with open(rss_feed) as rss_content:
        content = rss_content.read()

    page.content = content
    page.is_published = True
    page.content_type = "application/rss+xml"
    page.save()

    return page
