from django.urls import reverse
from django.test import TestCase

from ..models import Sponsor
from companies.models import Company


class SponsorViewTests(TestCase):
    def setUp(self):
        self.company1 = Company.objects.create(name='Python')

        self.Sponsor1 = Sponsor.objects.create(
            company=self.company1,
            is_published=True)

        self.company2 = Company.objects.create(name='Python Hidden')

        self.Sponsor2 = Sponsor.objects.create(
            company=self.company2,
            is_published=False)

    def test_sponsor_list(self):
        url = reverse('sponsor_list')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['sponsors']), 1)
