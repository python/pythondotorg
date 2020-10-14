import datetime

from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..forms import NewPSFBoardMeetingForm
from ..models import Minutes, Meeting
from ..meetings_factories import new_psf_board_meeting
from users.factories import UserFactory

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


class PreviewMeetingMinutesAdminViewTests(TestCase):

    def setUp(self):
        self.date = datetime.date.today()
        self.psf_board_meeting = new_psf_board_meeting(self.date)
        self.url = reverse("admin:minutes_meeting_preview_minutes", args=[self.psf_board_meeting.pk])
        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

    def test_login_required(self):
        self.client.logout()
        admin_login = reverse("admin:login")
        redirect_url = f"{admin_login}?next={self.url}"

        response = self.client.get(self.url)

        self.assertRedirects(response, redirect_url, fetch_redirect_response=False)

    def test_requires_permission(self):
        self.user.is_superuser = False
        self.user.is_staff = False
        self.user.save()
        admin_login = reverse("admin:login")
        redirect_url = f"{admin_login}?next={self.url}"

        response = self.client.get(self.url)

        self.assertRedirects(response, redirect_url, fetch_redirect_response=False)

    def test_404_if_meeting_does_not_exist(self):
        self.psf_board_meeting.delete()
        response = self.client.get(self.url)
        self.assertEqual(404, response.status_code)

    def test_create_draft_minute_and_redirect_to_preview(self):
        self.assertEqual(0, Minutes.objects.count())

        response = self.client.get(self.url)
        new_minutes = Minutes.objects.get()

        self.assertRedirects(response, new_minutes.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(self.psf_board_meeting, new_minutes.meeting)
        self.assertEqual(self.date, new_minutes.date)
        self.assertEqual(self.psf_board_meeting.get_content(), new_minutes.content.raw)
        self.assertEqual("markdown", new_minutes.content_markup_type)
        self.assertFalse(new_minutes.is_published)

    def test_update_existing_meeting_minutes(self):
        minutes = Minutes.objects.create(
            content='foo',
            is_published=False,
            date=self.date,
        )
        self.psf_board_meeting.minutes = minutes
        self.psf_board_meeting.save()

        response = self.client.get(self.url)
        minutes.refresh_from_db()

        self.assertRedirects(response, minutes.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(self.psf_board_meeting.get_content(), minutes.content.raw)
        self.assertEqual("markdown", minutes.content_markup_type)

    def test_do_not_update_content_if_minutes_were_already_published(self):
        minutes = Minutes.objects.create(
            content='previous content',
            is_published=True,
            date=self.date,
        )
        self.psf_board_meeting.minutes = minutes
        self.psf_board_meeting.save()

        response = self.client.get(self.url)
        minutes.refresh_from_db()

        self.assertRedirects(response, minutes.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual("previous content", minutes.content.raw)
        self.assertEqual("restructuredtext", minutes.content_markup_type)  # restructuredtext as default


class CreatePSFBoardMeetingAdminViewTests(TestCase):

    def setUp(self):
        self.date = datetime.date.today()
        self.url = reverse("admin:minutes_meeting_new_psf_board_meeting")
        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

    def test_login_required(self):
        self.client.logout()
        admin_login = reverse("admin:login")
        redirect_url = f"{admin_login}?next={self.url}"

        response = self.client.get(self.url)

        self.assertRedirects(response, redirect_url, fetch_redirect_response=False)

    def test_requires_permission(self):
        self.user.is_superuser = False
        self.user.is_staff = False
        self.user.save()
        admin_login = reverse("admin:login")
        redirect_url = f"{admin_login}?next={self.url}"

        response = self.client.get(self.url)

        self.assertRedirects(response, redirect_url, fetch_redirect_response=False)

    def test_render_html_with_simple_date_form(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "minutes/admin/new_psf_board_meeting_form.html")
        self.assertIsInstance(context["form"], NewPSFBoardMeetingForm)

    def test_create_new_meeting_with_valid_input(self):
        self.assertFalse(Meeting.objects.exists())
        response = self.client.post(self.url, data={"date": self.date})
        context = response.context

        psf_meeting = Meeting.objects.get()
        redirect_url = reverse("admin:minutes_meeting_change", args=[psf_meeting.pk])
        self.assertRedirects(response, redirect_url)

    def test_handle_errors_if_invalid_post_data(self):
        response = self.client.post(self.url, data={})

        self.assertFalse(Meeting.objects.exists())
        self.assertTemplateUsed(response, "minutes/admin/new_psf_board_meeting_form.html")
        self.assertTrue(response.context["form"].errors)
