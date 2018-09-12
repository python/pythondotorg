import datetime

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Minutes

User = get_user_model()


class MinutesViewsTests(TestCase):

    def setUp(self):
        start_date = datetime.datetime.now()
        last_month = start_date - datetime.timedelta(weeks=4)
        two_months = last_month - datetime.timedelta(weeks=4)

        self.m1 = Minutes.objects.create(
            date=start_date,
            content='Testing',
            is_published=False,
        )

        self.m2 = Minutes.objects.create(
            date=last_month,
            content='Testing',
            is_published=True,
        )

        self.m3 = Minutes.objects.create(
            date=two_months,
            content='Testing',
            is_published=True,
        )

        self.admin_user = User.objects.create_user('admin', 'admin@admin.com', 'adminpass')
        self.admin_user.is_staff = True
        self.admin_user.save()

    def test_list_view(self):
        response = self.client.get(reverse('minutes_list'))
        self.assertEqual(response.status_code, 200)

        self.assertNotIn(self.m1, response.context['minutes_list'])
        self.assertIn(self.m2, response.context['minutes_list'])
        self.assertIn(self.m3, response.context['minutes_list'])

        # Test that staff can see drafts
        self.client.login(username='admin', password='adminpass')

        response = self.client.get(reverse('minutes_list'))
        self.assertEqual(response.status_code, 200)

        self.assertIn(self.m1, response.context['minutes_list'])
        self.assertIn(self.m2, response.context['minutes_list'])
        self.assertIn(self.m3, response.context['minutes_list'])

    def test_detail_view(self):
        response = self.client.get(reverse('minutes_detail', kwargs={
            'year': self.m2.date.strftime("%Y"),
            'month': self.m2.date.strftime("%m").zfill(2),
            'day': self.m2.date.strftime("%d").zfill(2),
        }))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.m2, response.context['minutes'])

        response = self.client.get(reverse('minutes_detail', kwargs={
            'year': self.m1.date.strftime("%Y"),
            'month': self.m1.date.strftime("%m").zfill(2),
            'day': self.m1.date.strftime("%d").zfill(2),
        }))

        self.assertEqual(response.status_code, 404)

        # Test that staff can see drafts
        self.client.login(username='admin', password='adminpass')

        response = self.client.get(reverse('minutes_detail', kwargs={
            'year': self.m1.date.strftime("%Y"),
            'month': self.m1.date.strftime("%m").zfill(2),
            'day': self.m1.date.strftime("%d").zfill(2),
        }))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.m1, response.context['minutes'])
