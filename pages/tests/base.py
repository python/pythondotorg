from django.test import TestCase
from ..models import Page


class BasePageTests(TestCase):
    def setUp(self):
        self.p1 = Page.objects.create(title='One', path='one', content='Whatever', is_published=True)
        self.p2 = Page.objects.create(title='Two', path='two', content='Yup', is_published=False)
