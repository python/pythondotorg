from django.test import TestCase

from .models import CodeSample


class CodeSampleModelTests(TestCase):
    def setUp(self):
        self.sample2 = CodeSample.objects.create(
            code='Code One',
            copy='Copy One',
            is_published=True)

        self.sample2 = CodeSample.objects.create(
            code='Code Two',
            copy='Copy Two',
            is_published=False)

    def test_published(self):
        expected = ['<CodeSample: Copy One>']
        published_qs = CodeSample.objects.published()
        actual = [f'<CodeSample: {str(obj)}>' for obj in published_qs]
        self.assertEqual(actual, expected)

    def test_draft(self):
        expected = ['<CodeSample: Copy Two>']
        draft_qs = CodeSample.objects.draft()
        actual = [f'<CodeSample: {str(obj)}>' for obj in draft_qs]
        self.assertEqual(actual, expected)
