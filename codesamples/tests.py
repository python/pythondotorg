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
        self.assertQuerySetEqual(CodeSample.objects.published(),['<CodeSample: Copy One>'], transform=repr)

    def test_draft(self):
        self.assertQuerySetEqual(CodeSample.objects.draft(),['<CodeSample: Copy Two>'], transform=repr)
