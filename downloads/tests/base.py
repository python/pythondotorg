import datetime

from django.test import TestCase
from django.utils import timezone

from pages.models import Page
from boxes.models import Box
from ..models import OS, Release, ReleaseFile


class DownloadMixin:

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.download_supernav_box, _ = Box.objects.get_or_create(label='supernav-python-downloads')
        cls.download_supernav_box.content.markup_type = 'html'
        cls.download_supernav_box.save()
        cls.download_homepage_box, _ = Box.objects.get_or_create(label='homepage-downloads')
        cls.download_homepage_box.content.markup_type = 'html'
        cls.download_homepage_box.save()
        cls.download_sources_box, _ = Box.objects.get_or_create(label='download-sources')
        cls.windows, _ = OS.objects.get_or_create(name='Windows')
        cls.osx, _ = OS.objects.get_or_create(name='Mac OSX')
        cls.linux, _ = OS.objects.get_or_create(name='Linux')


class BaseDownloadTests(DownloadMixin, TestCase):

    def setUp(self):
        self.release_275_page = Page.objects.create(
            title='Python 2.7.5 Release',
            path='download/releases/2.7.5',
            content='whatever',
            is_published=True,
        )
        self.release_275 = Release.objects.create(
            version=Release.PYTHON2,
            name='Python 2.7.5',
            is_latest=True,
            is_published=True,
            release_page=self.release_275_page,
            release_date=timezone.now() - datetime.timedelta(days=-1)
        )
        self.release_275_windows_32bit = ReleaseFile.objects.create(
            os=self.windows,
            release=self.release_275,
            name='Windows x86 MSI Installer (2.7.5)',
            description='Windows binary -- does not include source',
            url='ftp/python/2.7.5/python-2.7.5.msi',
        )
        self.release_275_windows_64bit = ReleaseFile.objects.create(
            os=self.windows,
            release=self.release_275,
            name='Windows X86-64 MSI Installer (2.7.5)',
            description='Windows AMD64 / Intel 64 / X86-64 binary -- does not include source',
            url='ftp/python/2.7.5/python-2.7.5.amd64.msi'
        )

        self.release_275_osx = ReleaseFile.objects.create(
            os=self.osx,
            release=self.release_275,
            name='Mac OSX 64-bit/32-bit',
            description='Mac OS X 10.6 and later',
            url='ftp/python/2.7.5/python-2.7.5-macosx10.6.dmg',
        )

        self.release_275_linux = ReleaseFile.objects.create(
            name='Source tarball',
            os=self.linux,
            release=self.release_275,
            is_source=True,
            description='Gzipped source',
            url='ftp/python/2.7.5/Python-2.7.5.tgz',
        )

        self.draft_release = Release.objects.create(
            version=Release.PYTHON3,
            name='Python 9.7.2',
            is_published=False,
            release_page=self.release_275_page,
        )

        self.draft_release_linux = ReleaseFile.objects.create(
            name='Source tarball for a draft release',
            os=self.linux,
            release=self.draft_release,
            is_source=True,
            description='Gzipped source',
            url='ftp/python/9.7.2/Python-9.7.2.tgz',
        )

        self.hidden_release = Release.objects.create(
            version=Release.PYTHON3,
            name='Python 0.0.0',
            is_published=True,
            show_on_download_page=False,
            release_page=self.release_275_page,
        )

        self.pre_release = Release.objects.create(
            version=Release.PYTHON3,
            name='Python 3.9.90',
            is_published=True,
            pre_release=True,
            show_on_download_page=True,
            release_page=self.release_275_page,
        )

        self.python_3 = Release.objects.create(
            version=Release.PYTHON3,
            name='Python 3.10',
            is_latest=True,
            is_published=True,
            show_on_download_page=True,
            release_page=self.release_275_page
        )
