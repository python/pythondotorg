import io
from tempfile import TemporaryDirectory
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from rest_framework.authtoken.models import Token

from apps.sponsors.models import (
    FileAsset,
    ImgAsset,
    ProvidedFileAsset,
    ProvidedFileAssetConfiguration,
    SponsorContact,
)
from apps.sponsors.storage import get_asset_storage

CONTENT = b"%PDF-1.4 sponsor benefit file"


class PrivateAssetFilesTestBase(TestCase):
    def setUp(self):
        public_root = self.enterContext(TemporaryDirectory())
        private_root = self.enterContext(TemporaryDirectory())
        self.enterContext(self.settings(MEDIA_ROOT=public_root, SPONSORS_ASSET_STORAGE_ROOT=private_root))
        self.storage = get_asset_storage()
        for model, name in (
            (FileAsset, "file"),
            (ProvidedFileAsset, "shared_file"),
            (ProvidedFileAssetConfiguration, "shared_file"),
        ):
            self.enterContext(mock.patch.object(getattr(model, name).field, "storage", self.storage))
        self.sponsorship = baker.make_recipe("apps.sponsors.tests.finalized_sponsorship")
        self.sponsor = self.sponsorship.sponsor

    def make_sponsor_user(self, sponsor):
        user = baker.make(settings.AUTH_USER_MODEL)
        baker.make(SponsorContact, sponsor=sponsor, user=user)
        return user


class DownloadSponsorAssetViewTests(PrivateAssetFilesTestBase):
    def setUp(self):
        super().setUp()
        self.asset = FileAsset.objects.create(internal_name="deck", content_object=self.sponsorship)
        self.asset.file.save("deck.pdf", ContentFile(CONTENT))
        self.url = self.asset.file.url

    def assert_downloads(self, url=None, **kwargs):
        response = self.client.get(url or self.url, **kwargs)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), CONTENT)
        return response

    def test_uploaded_files_are_private_and_routed(self):
        self.assertEqual(self.url, reverse("download_sponsor_asset", args=[self.asset.file.name]))
        self.assertTrue(self.url.startswith("/sponsors/assets/sponsors-app-assets/"))
        self.assertTrue(self.asset.is_file)
        self.assertFalse(default_storage.exists(self.asset.file.name))

    def test_anonymous_users_are_sent_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL, response.url)

    def test_unrelated_users_and_staff_without_permissions_are_denied(self):
        other_sponsorship = baker.make_recipe("apps.sponsors.tests.finalized_sponsorship")
        for user in (
            self.make_sponsor_user(other_sponsorship.sponsor),
            baker.make(settings.AUTH_USER_MODEL, is_staff=True),
        ):
            with self.subTest(user=user):
                self.client.force_login(user)
                self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_own_sponsor_users_download_private_attachment(self):
        self.client.force_login(self.make_sponsor_user(self.sponsor))
        response = self.assert_downloads()
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_sponsor_level_uploads_are_visible_to_users_of_any_sponsorship_of_the_sponsor(self):
        asset = FileAsset.objects.create(internal_name="brand", content_object=self.sponsor)
        asset.file.save("brand.pdf", ContentFile(CONTENT))
        self.client.force_login(self.make_sponsor_user(self.sponsor))
        self.assert_downloads(asset.file.url)
        submitter = baker.make(settings.AUTH_USER_MODEL)
        baker.make_recipe("apps.sponsors.tests.finalized_sponsorship", sponsor=self.sponsor, submited_by=submitter)
        self.client.force_login(submitter)
        self.assert_downloads(asset.file.url)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_sponsorship_admin_group_and_permitted_staff_download(self):
        group, _ = Group.objects.get_or_create(name="Sponsorship Admin")
        member = baker.make(settings.AUTH_USER_MODEL)
        member.groups.add(group)
        self.client.force_login(member)
        self.assert_downloads()

        staff = baker.make(settings.AUTH_USER_MODEL, is_staff=True)
        permission = Permission.objects.get(codename="view_fileasset", content_type__app_label="sponsors")
        staff.user_permissions.add(permission)
        self.client.force_login(staff)
        self.assert_downloads()

    def test_publisher_api_token_downloads_without_session(self):
        publisher = baker.make(settings.AUTH_USER_MODEL)
        publisher.user_permissions.add(Permission.objects.get(codename="sponsor_publisher"))
        token = Token.objects.get(user=publisher)
        self.assert_downloads(headers={"authorization": f"Token {token.key}"})
        self.assertEqual(self.client.get(self.url, headers={"authorization": "Token invalid"}).status_code, 403)

        unprivileged = Token.objects.get(user=baker.make(settings.AUTH_USER_MODEL))
        response = self.client.get(self.url, headers={"authorization": f"Token {unprivileged.key}"})
        self.assertEqual(response.status_code, 403)

    def test_untracked_and_missing_names_are_not_served(self):
        self.storage.save("untracked.pdf", ContentFile(CONTENT))
        self.client.force_login(baker.make(settings.AUTH_USER_MODEL, is_superuser=True))
        for name in ("untracked.pdf", "missing.pdf", "../../outside.pdf"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse("download_sponsor_asset", args=[name])).status_code, 404)
        self.storage.delete(self.asset.file.name)
        self.assertEqual(self.client.get(self.url).status_code, 404)

        self.client.force_login(self.make_sponsor_user(self.sponsor))
        untracked_url = reverse("download_sponsor_asset", args=["untracked.pdf"])
        self.assertEqual(self.client.get(untracked_url).status_code, 403)


class ProvidedFileDownloadTests(PrivateAssetFilesTestBase):
    def setUp(self):
        super().setUp()
        self.configuration = baker.make(ProvidedFileAssetConfiguration, internal_name="guide", related_to="sponsorship")
        self.configuration.shared_file.save("Exhibitor Guide.pdf", ContentFile(CONTENT))
        self.url = self.configuration.shared_file.url

    def test_provided_files_keep_their_name_under_an_unguessable_directory(self):
        name_pattern = r"^sponsors-provided-files/[0-9a-f]{32}/Exhibitor_Guide\.pdf$"
        self.assertRegex(self.configuration.shared_file.name, name_pattern)
        self.assertEqual(self.url, reverse("download_sponsor_asset", args=[self.configuration.shared_file.name]))
        self.assertFalse(default_storage.exists(self.configuration.shared_file.name))
        self.client.force_login(baker.make(settings.AUTH_USER_MODEL, is_superuser=True))
        response = self.client.get(self.url)
        self.assertEqual(b"".join(response.streaming_content), CONTENT)
        self.assertIn('filename="Exhibitor_Guide.pdf"', response["Content-Disposition"])

    def test_configuration_only_files_are_limited_to_managers(self):
        user = self.make_sponsor_user(self.sponsor)
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

        baker.make(
            ProvidedFileAsset,
            sponsor_benefit__sponsorship=self.sponsorship,
            internal_name="guide",
            related_to="sponsorship",
            shared_file=self.configuration.shared_file.name,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), CONTENT)

        other_user = self.make_sponsor_user(baker.make_recipe("apps.sponsors.tests.finalized_sponsorship").sponsor)
        self.client.force_login(other_user)
        self.assertEqual(self.client.get(self.url).status_code, 403)


class SponsorshipAssetsAPIFileURLTests(PrivateAssetFilesTestBase):
    def setUp(self):
        super().setUp()
        publisher = baker.make(settings.AUTH_USER_MODEL)
        publisher.user_permissions.add(Permission.objects.get(codename="sponsor_publisher"))
        self.authorization = f"Token {Token.objects.get(user=publisher).key}"

    def get_values(self, internal_name):
        url = reverse("assets_list") + f"?internal_name={internal_name}"
        response = self.client.get(url, headers={"authorization": self.authorization})
        self.assertEqual(response.status_code, 200)
        return [item["value"] for item in response.json()]

    def test_files_are_absolute_private_urls_and_images_stay_public(self):
        file_asset = FileAsset.objects.create(internal_name="deck", content_object=self.sponsorship)
        file_asset.file.save("deck.pdf", ContentFile(CONTENT))
        image = ImgAsset.objects.create(internal_name="logo", content_object=self.sponsor)
        image.image = SimpleUploadedFile("logo.png", b"img", content_type="image/png")
        image.save()

        self.assertEqual(self.get_values("deck"), [f"http://testserver{file_asset.file.url}"])
        self.assertEqual(self.get_values("logo"), [f"{settings.MEDIA_URL}sponsors-app-assets/{image.uuid}.png"])
        self.assertTrue(default_storage.exists(image.image.name))


class RemediateSponsorAssetStorageCommandTests(PrivateAssetFilesTestBase):
    def setUp(self):
        super().setUp()
        self.upload = default_storage.save("sponsors-app-assets/legacy.pdf", ContentFile(CONTENT))
        asset = FileAsset.objects.create(internal_name="deck", content_object=self.sponsorship)
        FileAsset.objects.filter(pk=asset.pk).update(file=self.upload)
        self.provided = default_storage.save("signed_contract.pdf", ContentFile(CONTENT))
        baker.make(ProvidedFileAssetConfiguration, internal_name="guide", shared_file=self.provided)
        baker.make(ProvidedFileAsset, sponsor_benefit__sponsorship=self.sponsorship, shared_file=self.provided)
        self.image = default_storage.save("sponsors-app-assets/logo.png", ContentFile(b"img"))
        image_asset = ImgAsset.objects.create(internal_name="logo", content_object=self.sponsor)
        ImgAsset.objects.filter(pk=image_asset.pk).update(image=self.image)
        self.names = (self.upload, self.provided)

    def run_command(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        call_command("remediate_sponsor_asset_storage", *args, stdout=stdout, stderr=stderr)
        return stdout.getvalue() + stderr.getvalue()

    def assert_public_image_untouched(self, output):
        self.assertNotIn(self.image, output)
        self.assertTrue(default_storage.exists(self.image))
        self.assertFalse(self.storage.exists(self.image))

    def test_dry_run_reports_without_copying(self):
        output = self.run_command()
        for name in self.names:
            self.assertIn(f"[legacy public] {name}", output)
            self.assertFalse(self.storage.exists(name))
            self.assertTrue(default_storage.exists(name))
        self.assert_public_image_untouched(output)

    def test_copy_then_explicit_public_removal_is_verified_and_idempotent(self):
        self.run_command("--apply")
        for name in self.names:
            self.assertTrue(default_storage.exists(name))
            with self.storage.open(name) as migrated:
                self.assertEqual(migrated.read(), CONTENT)
        self.run_command("--apply", "--delete-legacy")
        output = self.run_command("--apply", "--delete-legacy")
        for name in self.names:
            self.assertFalse(default_storage.exists(name))
            self.assertTrue(self.storage.exists(name))
        self.assert_public_image_untouched(output)

    def test_mismatching_private_copy_prevents_public_deletion(self):
        self.storage.save(self.upload, ContentFile(b"wrong file"))
        with self.assertRaises(CommandError):
            self.run_command("--apply", "--delete-legacy")
        self.assertTrue(default_storage.exists(self.upload))

    def test_deletion_requires_explicit_apply(self):
        with self.assertRaises(CommandError):
            self.run_command("--delete-legacy")
        self.assertTrue(default_storage.exists(self.upload))
