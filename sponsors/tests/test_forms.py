from django.test import TestCase

from sponsors.forms import SponsorshiptBenefitsForm


class SponsorshiptBenefitsFormTests(TestCase):

    def test_required_fields(self):
        required_fields = ["benefits"]

        form = SponsorshiptBenefitsForm(data={})

        self.assertFalse(form.is_valid())
        self.assertEqual(len(required_fields), len(form.errors))
        for required in required_fields:
            self.assertIn(required, form.errors)
