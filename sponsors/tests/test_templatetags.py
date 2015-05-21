from django.test import TestCase

from companies.models import Company

from ..models import Sponsor
from ..templatetags.sponsors import featured_sponsor_rotation


class SponsorTemplatetagTests(TestCase):

    def test_templatetag(self):
        company = Company.objects.create(name='Featured Company')
        sponsor = Sponsor.objects.create(
            company=company,
            is_published=True,
            featured=True,
        )
        sponsors_context = featured_sponsor_rotation()
        self.assertIn(sponsor, sponsors_context['sponsors'])
