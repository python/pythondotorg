"""Tests for mailing app forms."""
from django.test import TestCase

from mailing.tests.forms import TestBaseEmailTemplateForm


class BaseEmailTemplateFormTests(TestCase):

    def setUp(self):
        self.data = {
            "content": "Hi, {{ name }}\n\nThis is a message to you.",
            "subject": "Hello",
            "internal_name": "notification 01",
        }

    def test_validate_required_fields(self):
        required = set(self.data)
        form = TestBaseEmailTemplateForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(required, set(form.errors))

    def test_validate_with_correct_data(self):
        form = TestBaseEmailTemplateForm(data=self.data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_if_broken_template_syntax(self):
        self.data["content"] = "Invalid syntax {% invalid %}"
        form = TestBaseEmailTemplateForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors, form.errors)
