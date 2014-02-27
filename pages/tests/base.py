from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Page

User = get_user_model()


class BasePageTests(TestCase):
    def setUp(self):
        self.p1 = Page.objects.create(title='One', path='one', content='Whatever', is_published=True)
        self.p2 = Page.objects.create(title='Two', path='two', content='Yup', is_published=False)

        self.staff_user = User.objects.create_user(username='staff_user', password='staff_user')
        self.staff_user.is_staff = True
        self.staff_user.save()
