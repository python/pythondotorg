from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from sponsors.forms import SponsorUpdateForm, SponsorRequiredAssetsForm
from sponsors.models import Sponsorship, RequiredTextAssetConfiguration, SponsorBenefit
from sponsors.models.enums import AssetsRelatedTo
from sponsors.tests.utils import get_static_image_file_as_upload
from users.factories import UserFactory
from users.models import Membership

User = get_user_model()


class UsersViewsTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(
            username='username',
            password='password',
            email='niklas@sundin.se',
            search_visibility=User.SEARCH_PUBLIC,
            membership=None,
        )
        self.user2 = UserFactory(
            username='spameggs',
            password='password',
            search_visibility=User.SEARCH_PRIVATE,
            email_privacy=User.EMAIL_PRIVATE,
            public_profile=False,
        )

    def assertUserCreated(self, data=None, template_name='account/verification_sent.html'):
        post_data = {
            'username': 'guido',
            'email': 'montyopython@python.org',
            'password1': 'password',
            'password2': 'password',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        post_data.update(data or {})
        url = reverse('account_signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name)
        user = User.objects.get(username=post_data['username'])
        self.assertEqual(user.username, post_data['username'])
        self.assertEqual(user.email, post_data['email'])
        return response

    def test_membership_create(self):
        url = reverse('users:user_membership_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Requires login now

        self.client.login(username='username', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'legal_name': 'Some Name',
            'preferred_name': 'Sommy',
            'email_address': 'sommy@example.com',
            'city': 'Lawrence',
            'region': 'Kansas',
            'country': 'USA',
            'postal_code': '66044',
            'psf_code_of_conduct': True,
            'psf_announcements': True,
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:user_membership_thanks'))

    def test_membership_update(self):
        url = reverse('users:user_membership_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Requires login now

        self.assertTrue(self.user2.has_membership)
        self.client.login(username=self.user2.username, password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'legal_name': 'Some Name',
            'preferred_name': 'Sommy',
            'email_address': 'sommy@example.com',
            'city': 'Lawrence',
            'region': 'Kansas',
            'country': 'USA',
            'postal_code': '66044',
            'psf_announcements': True,
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

    def test_membership_update_404(self):
        url = reverse('users:user_membership_edit')
        self.assertFalse(self.user.has_membership)
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_has_already_have_membership(self):
        # Should redirect to /membership/edit/ if user already
        # has membership.
        url = reverse('users:user_membership_create')
        self.assertTrue(self.user2.has_membership)
        self.client.login(username=self.user2.username, password='password')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('users:user_membership_edit'))

    def test_user_update(self):
        self.client.login(username='username', password='password')
        url = reverse('users:user_profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)

    def test_user_update_redirect(self):
        # see issue #925
        self.client.login(username='username', password='password')
        url = reverse('users:user_profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # should return 200 if the user does want to see their user profile
        post_data = {
            'username': 'username',
            'search_visibility': 0,
            'email_privacy': 1,
            'public_profile': False,
            'email': 'niklas@sundin.se',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        response = self.client.post(url, post_data)
        profile_url = reverse('users:user_detail', kwargs={'slug': 'username'})
        self.assertRedirects(response, profile_url)

        # should return 404 for another user
        another_user_url = reverse('users:user_detail', kwargs={'slug': 'spameggs'})
        response = self.client.get(another_user_url)
        self.assertEqual(response.status_code, 404)

        # should return 404 if the user is not logged-in
        self.client.logout()
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 404)

    def test_user_detail(self):
        # Ensure detail page is viewable without login, but that edit URLs
        # do not appear
        detail_url = reverse('users:user_detail', kwargs={'slug': self.user.username})
        edit_url = reverse('users:user_profile_edit')
        response = self.client.get(detail_url)
        self.assertTrue(self.user.is_active)
        self.assertNotContains(response, edit_url)

        # Ensure edit url is available to logged in users
        self.client.login(username='username', password='password')
        response = self.client.get(detail_url)
        self.assertContains(response, edit_url)

        # Ensure inactive accounts shouldn't be shown to users.
        user = User.objects.create_user(
            username='foobar',
            password='baz',
            email='paradiselost@example.com',
        )
        user.is_active = False
        user.save()
        self.assertFalse(user.is_active)
        detail_url = reverse('users:user_detail', kwargs={'slug': user.username})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)

    def test_special_usernames(self):
        # Ensure usernames in the forms of:
        # first.last
        # user@host.com
        # are allowed to view their profile pages since we allow them in
        # the username field
        u1 = User.objects.create_user(
            username='user.name',
            password='password',
        )
        detail_url = reverse('users:user_detail', kwargs={'slug': u1.username})
        edit_url = reverse('users:user_profile_edit')

        self.client.login(username=u1.username, password='password')
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        u2 = User.objects.create_user(
            username='user@example.com',
            password='password',
        )

        detail_url = reverse('users:user_detail', kwargs={'slug': u2.username})
        edit_url = reverse('users:user_profile_edit')

        self.client.login(username=u2.username, password='password')
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

    def test_user_new_account(self):
        self.assertUserCreated(data={
            'username': 'thisusernamedoesntexist',
            'email': 'thereisnoemail@likesthis.com',
            'password1': 'password',
            'password2': 'password',
        })

    def test_user_duplicate_username_email(self):
        post_data = {
            'username': 'thisusernamedoesntexist',
            'email': 'thereisnoemail@likesthis.com',
            'password1': 'password',
            'password2': 'password',
        }
        self.assertUserCreated(data=post_data)
        response = self.assertUserCreated(
            data=post_data, template_name='account/signup.html'
        )
        self.assertContains(
            response, 'A user with that username already exists.'
        )
        self.assertContains(
            response, 'A user is already registered with this email address.'
        )

    def test_usernames(self):
        url = reverse('account_signup')
        usernames = [
            'foaso+bar', 'foo.barahgs', 'foo@barbazbaz',
            'foo.baarBAZ',
        ]
        post_data = {
            'username': 'thisusernamedoesntexist',
            'email': 'thereisnoemail@likesthis.com',
            'password1': 'password',
            'password2': 'password',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        for i, username in enumerate(usernames):
            with self.subTest(i=i, username=username):
                post_data.update({
                    'username': username,
                    'email': f'foo{i}@example.com'
                })
                response = self.client.post(url, post_data, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'account/verification_sent.html')

    def test_is_active_login(self):
        # 'allauth.account.auth_backends.AuthenticationBackend'
        # doesn't reject inactive users (but
        # 'django.contrib.auth.backends.ModelBackend' does since
        # Django 1.10) so if we use 'self.client.login()' it will
        # return True. The actual rejection performs by the
        # 'perform_login()' helper and it redirects inactive users
        # to a separate view.
        url = reverse('account_login')
        user = UserFactory(is_active=False)
        data = {'login': user.username, 'password': 'password'}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('account_inactive'))
        url = reverse('users:user_membership_create')
        response = self.client.get(url)
        # Ensure that an inactive user didn't get logged in.
        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('account_login'), url)
        )

    def test_user_delete_needs_to_be_logged_in(self):
        url = reverse('users:user_delete', kwargs={'slug': self.user.username})
        response = self.client.delete(url)
        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('account_login'), url)
        )

    def test_user_delete_invalid_request_method(self):
        url = reverse('users:user_delete', kwargs={'slug': self.user.username})
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_user_delete_different_user(self):
        url = reverse('users:user_delete', kwargs={'slug': self.user.username})
        self.client.login(username=self.user2.username, password='password')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_user_delete(self):
        url = reverse('users:user_delete', kwargs={'slug': self.user.username})
        self.client.login(username=self.user.username, password='password')
        response = self.client.delete(url)
        self.assertRedirects(response, reverse('home'))
        self.assertRaises(User.DoesNotExist, User.objects.get, username=self.user.username)
        self.assertRaises(Membership.DoesNotExist, Membership.objects.get, creator=self.user)

    def test_membership_delete_needs_to_be_logged_in(self):
        url = reverse('users:user_membership_delete', kwargs={'slug': self.user2.username})
        response = self.client.delete(url)
        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('account_login'), url)
        )

    def test_membership_delete_invalid_request_method(self):
        url = reverse('users:user_membership_delete', kwargs={'slug': self.user2.username})
        self.client.login(username=self.user2.username, password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_membership_delete_different_user_membership(self):
        user = UserFactory()
        self.assertTrue(user.has_membership)
        url = reverse('users:user_membership_delete', kwargs={'slug': user.username})
        self.client.login(username=self.user2.username, password='password')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_membership_does_not_exist(self):
        self.assertFalse(self.user.has_membership)
        url = reverse('users:user_membership_delete', kwargs={'slug': self.user.username})
        self.client.login(username=self.user.username, password='password')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_membership_delete(self):
        self.assertTrue(self.user2.has_membership)
        url = reverse('users:user_membership_delete', kwargs={'slug': self.user2.username})
        self.client.login(username=self.user2.username, password='password')
        response = self.client.delete(url)
        self.assertRedirects(
            response,
            reverse('users:user_detail', kwargs={'slug': self.user2.username})
        )
        # TODO: We can't use 'self.user2.refresh_from_db()' because
        # of https://code.djangoproject.com/ticket/27846.
        with self.assertRaises(Membership.DoesNotExist):
            Membership.objects.get(pk=self.user2.membership.pk)

    def test_password_change_honeypot(self):
        url = reverse('account_change_password')
        data = {
            'oldpassword': 'password',
            'password1': 'newpassword',
            'password2': 'newpassword',
        }
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(url, data, follow=True)
        # We should get 400 without 'HONEYPOT_FIELD_NAME'
        # field in the post data.
        self.assertEqual(response.status_code, 400)
        data[settings.HONEYPOT_FIELD_NAME] = settings.HONEYPOT_VALUE
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, reverse('users:user_profile_edit'))
        self.client.logout()
        logged_in = self.client.login(username=self.user.username,
                                      password='newpassword')
        self.assertTrue(logged_in)


class SponsorshipDetailViewTests(TestCase):

    def setUp(self):
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.client.force_login(self.user)
        self.sponsorship = baker.make(
            Sponsorship, submited_by=self.user, status=Sponsorship.APPLIED, _fill_optional=True
        )
        self.url = reverse(
            "users:sponsorship_application_detail", args=[self.sponsorship.pk]
        )

    def test_display_template_with_sponsorship_info(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "users/sponsorship_detail.html")
        self.assertEqual(context["sponsorship"], self.sponsorship)

    def test_404_if_sponsorship_does_not_exist(self):
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = settings.LOGIN_URL
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_404_if_sponsorship_does_not_belong_to_user(self):
        self.client.force_login(baker.make(settings.AUTH_USER_MODEL))  # log in with a new user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_list_assets(self):
        cfg = baker.make(RequiredTextAssetConfiguration, internal_name='input')
        benefit = baker.make(SponsorBenefit, sponsorship=self.sponsorship)
        asset = cfg.create_benefit_feature(benefit)

        response = self.client.get(self.url)
        context = response.context

        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(context["required_assets"]))
        self.assertIn(asset, context["required_assets"])
        self.assertEqual(0, len(context["fulfilled_assets"]))

    def test_fulfilled_assets(self):
        cfg = baker.make(RequiredTextAssetConfiguration, internal_name='input')
        benefit = baker.make(SponsorBenefit, sponsorship=self.sponsorship)
        asset = cfg.create_benefit_feature(benefit)
        asset.value = "information"
        asset.save()

        response = self.client.get(self.url)
        context = response.context

        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(context["required_assets"]))
        self.assertEqual(1, len(context["fulfilled_assets"]))
        self.assertIn(asset, context["fulfilled_assets"])

    def test_asset_links_are_direct(self) -> None:
        """Ensure that assets listed under 'Provided Assets' in `/users/sponsorships/#/` are directly accessible."""
        # Create a sponsorship with a provided file asset
        cfg = baker.make(
            "sponsors.ProvidedFileAssetConfiguration",
            internal_name="test_provided_file_asset",
            related_to="sponsorship",
        )
        benefit = baker.make("sponsors.SponsorBenefit",sponsorship=self.sponsorship)
        asset = cfg.create_benefit_feature(benefit)
        file_content = b"This is a test file."
        test_file = SimpleUploadedFile(
            "test_file.pdf",
            file_content,
            content_type="application/pdf"
        )
        asset.value = test_file
        asset.save()

        # Then we can read the page
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")
        expected_asset_link = f'href="{asset.value.url}"'

        # and finally check that the asset link is ACTUALLY pointing to the asset and not the list view page
        self.assertIn("View File", content, "View file text not found.")
        self.assertIn(expected_asset_link, content, "Asset link not found in the page.")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/sponsorship_detail.html")


class UpdateSponsorInfoViewTests(TestCase):

    def setUp(self):
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.client.force_login(self.user)
        self.sponsorship = baker.make(
            Sponsorship, submited_by=self.user, status=Sponsorship.APPLIED, _fill_optional=True
        )
        self.sponsor = self.sponsorship.sponsor
        self.contact = baker.make("sponsors.SponsorContact", sponsor=self.sponsor)
        self.url = reverse(
            "users:edit_sponsor_info", args=[self.sponsor.pk]
        )
        self.data = {
            "description": "desc",
            "name": "CompanyX",
            "primary_phone": "+14141413131",
            "mailing_address_line_1": "4th street",
            "city": "New York",
            "postal_code": "10212",
            "country": "US",
            "contact-0-id": self.contact.pk,
            "contact-0-name": "John",
            "contact-0-email": "email@email.com",
            "contact-0-phone": "+1999999999",
            "contact-0-primary": True,
            "contact-TOTAL_FORMS": 1,
            "contact-MAX_NUM_FORMS": 5,
            "contact-MIN_NUM_FORMS": 1,
            "contact-INITIAL_FORMS": 1,
            "web_logo": get_static_image_file_as_upload("psf-logo.png", "logo.png"),
            "print_logo": get_static_image_file_as_upload("psf-logo_print.png", "logo_print.png"),
        }

    def test_display_template_with_sponsor_info(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/new_sponsorship_application_form.html")
        self.assertEqual(context["sponsor"], self.sponsor)
        self.assertIsInstance(context["form"], SponsorUpdateForm)

    def test_404_if_sponsor_does_not_exist(self):
        self.sponsor.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_404_if_sponsor_from_sponsorship_from_another_user(self):
        sponsorship = baker.make(Sponsorship, _fill_optional=True)
        self.url = reverse(
            "users:edit_sponsor_info", args=[sponsorship.sponsor.pk]
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_render_form_with_errors(self):
        self.data = {}
        response = self.client.post(self.url, data=self.data)
        form = response.context["form"]
        self.assertEqual(200, response.status_code)
        self.assertTrue(form.errors)

    def test_update_sponsor_and_contact(self):
        response = self.client.post(self.url, data=self.data)

        self.sponsor.refresh_from_db()
        self.contact.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual("desc", self.sponsor.description)
        self.assertEqual("John", self.contact.name)


class UpdateSponsorshipAssetsViewTests(TestCase):

    def setUp(self):
        self.user = baker.make(User)
        self.sponsorship = baker.make(Sponsorship, sponsor__name="foo", submited_by=self.user)
        self.required_text_cfg = baker.make(
            RequiredTextAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSORSHIP.value,
            internal_name="Text Input",
            _fill_optional=True,
        )
        self.benefit = baker.make(SponsorBenefit, sponsorship=self.sponsorship)
        self.required_asset = self.required_text_cfg.create_benefit_feature(self.benefit)
        self.client.force_login(self.user)
        self.url = reverse("users:update_sponsorship_assets", args=[self.sponsorship.pk])

    def test_render_expected_html_and_context(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "users/sponsorship_assets_update.html")
        self.assertEqual(self.sponsorship, context["sponsorship"])
        self.assertEqual(self.sponsorship, context["form"].sponsorship)
        self.assertIsInstance(context["form"], SponsorRequiredAssetsForm)

    def test_render_form_for_specific_asset_if_informed_via_querystring(self):
        extra_required_text_cfg = baker.make(
            RequiredTextAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSORSHIP.value,
            internal_name="Second Text Input",
            _fill_optional=True,
        )
        req_asset = extra_required_text_cfg.create_benefit_feature(self.benefit)

        response = self.client.get(self.url + f"?required_asset={req_asset.pk}")
        form = response.context["form"]

        self.assertEqual(1, len(form.fields))
        self.assertIn("second_text_input", form.fields)

    def test_update_assets_information_with_valid_post(self):
        response = self.client.post(self.url, data={"text_input": "information"})
        context = response.context

        self.assertRedirects(response, reverse("users:sponsorship_application_detail", args=[self.sponsorship.pk]))
        self.assertEqual(self.required_asset.value, "information")

    def test_render_form_with_errors_when_updating_info_with_invalid_post(self):
        self.client.post(self.url, data={"text_input": "information"})  # first post updates the asset value

        response = self.client.post(self.url, {})
        context = response.context

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "users/sponsorship_assets_update.html")
        self.assertFalse(context["form"].is_valid())

    def test_404_if_sponsorship_does_not_exist(self):
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(404, response.status_code)

    def test_404_if_sponsorship_does_not_belong_to_user(self):
        other_user = baker.make(User)
        self.client.force_login(other_user)
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(404, response.status_code)
