from django.test import TestCase

from ..models import Sponsor
from companies.models import Company


class SponsorModelTests(TestCase):
    def setUp(self):
        self.company1 = Company.objects.create(name='Python')

        self.Sponsor1 = Sponsor.objects.create(
            company=self.company1,
            is_published=True)

        self.company2 = Company.objects.create(name='Python Hidden')

        self.Sponsor2 = Sponsor.objects.create(
            company=self.company2,
            is_published=False)

    def test_draft(self):
        self.assertQuerysetEqual(Sponsor.objects.draft(), ['<Sponsor: Python Hidden>'])

    def test_published(self):
        self.assertQuerysetEqual(Sponsor.objects.published(), ['<Sponsor: Python>'])
