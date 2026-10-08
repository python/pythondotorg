"""Regression coverage for sponsorship lifecycle fixes in the sponsor management UI."""

from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker

from apps.sponsors.exceptions import InvalidStatusError
from apps.sponsors.manage.tests import SponsorshipReviewTestBase
from apps.sponsors.models import Contract, Sponsorship, SponsorshipPackage
from apps.sponsors.utils import with_article
from apps.sponsors.validators import MAX_SIGNED_CONTRACT_BYTES


class WithArticleTests(SponsorshipReviewTestBase):
    def test_vowel_and_consonant(self):
        self.assertEqual(with_article("Approved"), "an Approved")
        self.assertEqual(with_article("Draft"), "a Draft")

    def test_model_error_grammar(self):
        self.sponsorship.status = Sponsorship.APPROVED
        with self.assertRaisesMessage(InvalidStatusError, "Can't approve an Approved sponsorship."):
            self.sponsorship.approve(None, None)


class SponsorshipEditTests(SponsorshipReviewTestBase):
    def setUp(self):
        super().setUp()
        self.sponsorship.status = Sponsorship.APPROVED
        self.sponsorship.save()
        Sponsorship.objects.filter(pk=self.sponsorship.pk).update(locked=False)

    def _edit(self, **data):
        payload = {"package": self.package.pk, "sponsorship_fee": 150000, "year": self.year, **data}
        return self.client.post(reverse("manage_sponsorship_edit", args=[self.sponsorship.pk]), payload)

    def test_edit_keeps_sponsorship_unlocked_and_logs(self):
        self._edit(sponsorship_fee=1000)
        self.sponsorship.refresh_from_db()
        self.assertFalse(self.sponsorship.locked)
        self.assertEqual(self.sponsorship.sponsorship_fee, 1000)
        self.assertTrue(LogEntry.objects.filter(object_id=str(self.sponsorship.pk)).exists())

    def test_package_change_marks_custom_package(self):
        baker.make("sponsors.SponsorBenefit", sponsorship=self.sponsorship)
        other = baker.make(SponsorshipPackage, name="Other", sponsorship_amount=1, year=self.year)
        response = self._edit(package=other.pk)
        self.sponsorship.refresh_from_db()
        self.assertTrue(self.sponsorship.for_modified_package)
        self.assertContains(self.client.get(response.url), "marked as a custom package")

    def test_locked_get_redirects(self):
        Sponsorship.objects.filter(pk=self.sponsorship.pk).update(locked=True)
        response = self.client.get(reverse("manage_sponsorship_edit", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)


class SponsorshipListTests(SponsorshipReviewTestBase):
    def setUp(self):
        super().setUp()
        self.other = baker.make(
            Sponsorship, sponsor__name="Zeta Ltd", package=self.package, year=self.year - 1, sponsorship_fee=5
        )

    def _list(self, **params):
        return self.client.get(reverse("manage_sponsorships"), params)

    def test_server_side_sort_is_global(self):
        names = [sp.sponsor.name for sp in self._list(sort="-sponsor", year="all").context["sponsorships"]]
        self.assertEqual(names, ["Zeta Ltd", "Acme Corp"])
        names = [sp.sponsor.name for sp in self._list(sort="fee", year="all").context["sponsorships"]]
        self.assertEqual(names, ["Zeta Ltd", "Acme Corp"])

    def test_sponsor_filter(self):
        response = self._list(sponsor=self.other.sponsor_id)
        self.assertEqual(list(response.context["sponsorships"]), [self.other])
        self.assertEqual(list(self._list(sponsor="abc").context["sponsorships"]), [])

    def test_out_of_range_page_clamps(self):
        self.assertEqual(self._list(page="999").status_code, 200)
        self.assertEqual(self._list(page="x").status_code, 200)

    def test_year_all_and_pill_counts_follow_filters(self):
        response = self._list(year="all")
        self.assertEqual(len(response.context["sponsorships"]), 2)
        response = self._list(year=str(self.year))
        self.assertEqual(response.context["count_applied"], 1)
        self.assertEqual(self._list(search="zeta").context["count_applied"], 1)

    def test_filter_links_are_urlencoded(self):
        response = self._list(search="A&B Co")
        self.assertIn("search=A%26B+Co", response.context["filter_query"])

    def test_bulk_redirect_keeps_filters(self):
        response = self.client.post(
            reverse("manage_bulk_action"), {"action": "export_csv", "return_query": "status=applied&year=all"}
        )
        self.assertEqual(response.url, reverse("manage_sponsorships") + "?status=applied&year=all")


class SponsorshipCsvTests(SponsorshipReviewTestBase):
    def test_filtered_csv_has_bom_charset_and_filename(self):
        response = self.client.get(reverse("manage_sponsorship_export"), {"status": "applied", "year": self.year})
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn(f"sponsorships-applied-{self.year}.csv", response["Content-Disposition"])
        self.assertTrue(response.content.decode("utf-8").startswith("\ufeff"))

    def test_detail_csv_exports_only_this_sponsorship(self):
        baker.make(Sponsorship, sponsor__name="Other", package=self.package, year=self.year)
        detail = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertContains(detail, f"?selected_ids={self.sponsorship.pk}")
        response = self.client.get(reverse("manage_sponsorship_export"), {"selected_ids": self.sponsorship.pk})
        rows = response.content.decode("utf-8").strip().splitlines()
        self.assertEqual(len(rows), 2)
        self.assertIn("Acme Corp", rows[1])


class InvalidStateActionTests(SponsorshipReviewTestBase):
    def test_approve_page_redirects_when_not_approvable(self):
        Sponsorship.objects.filter(pk=self.sponsorship.pk).update(status=Sponsorship.REJECTED)
        for name in ("manage_sponsorship_approve", "manage_sponsorship_approve_signed"):
            response = self.client.get(reverse(name, args=[self.sponsorship.pk]))
            self.assertRedirects(
                response,
                reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]),
                fetch_redirect_response=False,
            )

    def test_send_and_execute_pages_redirect_without_usable_contract(self):
        for name in ("manage_contract_send", "manage_contract_execute"):
            response = self.client.get(reverse(name, args=[self.sponsorship.pk]))
            self.assertEqual(response.status_code, 302)

    def test_reject_message_says_no_email_sent_yet(self):
        response = self.client.post(
            reverse("manage_sponsorship_reject", args=[self.sponsorship.pk]), {"action": "reject_notify"}, follow=True
        )
        self.assertContains(response, "No email has been sent yet")
        self.assertTrue(LogEntry.objects.filter(change_message="Sponsorship Rejected").exists())


class ContractLifecycleTests(SponsorshipReviewTestBase):
    def setUp(self):
        super().setUp()
        Sponsorship.objects.filter(pk=self.sponsorship.pk).update(status=Sponsorship.APPROVED, locked=True)
        self.sponsorship.refresh_from_db()
        self.contract = Contract.new(self.sponsorship)

    def _detail(self):
        return self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))

    def test_rollback_hidden_with_guidance_when_contract_awaiting_signature(self):
        Contract.objects.filter(pk=self.contract.pk).update(status=Contract.AWAITING_SIGNATURE)
        response = self._detail()
        self.assertFalse(response.context["can_rollback"])
        self.assertIn("nullify and then re-draft", response.context["rollback_hint"])

    def test_rollback_offered_for_draft_contract(self):
        self.assertTrue(self._detail().context["can_rollback"])

    def test_regenerate_offered_only_when_unlocked_and_not_executed(self):
        self.assertFalse(self._detail().context["can_regenerate"])
        Sponsorship.objects.filter(pk=self.sponsorship.pk).update(locked=False)
        self.assertTrue(self._detail().context["can_regenerate"])
        Contract.objects.filter(pk=self.contract.pk).update(status=Contract.EXECUTED)
        self.assertFalse(self._detail().context["can_regenerate"])

    def test_execute_shows_validator_errors_on_form(self):
        Contract.objects.filter(pk=self.contract.pk).update(status=Contract.AWAITING_SIGNATURE)
        upload = SimpleUploadedFile("signed.pdf", b"not a pdf", content_type="application/pdf")
        response = self.client.post(
            reverse("manage_contract_execute", args=[self.sponsorship.pk]), {"signed_document": upload}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("signed_document", response.context["form"].errors)

    def test_signed_contract_size_cap(self):
        Contract.objects.filter(pk=self.contract.pk).update(status=Contract.AWAITING_SIGNATURE)
        upload = SimpleUploadedFile("signed.pdf", b"%PDF-" + b"0" * MAX_SIGNED_CONTRACT_BYTES + b"%%EOF")
        response = self.client.post(
            reverse("manage_contract_execute", args=[self.sponsorship.pk]), {"signed_document": upload}
        )
        self.assertContains(response, "Upload at most 20 MB.")


class AssetExportTests(SponsorshipReviewTestBase):
    def test_no_assets_redirects_instead_of_500(self):
        response = self.client.get(reverse("manage_sponsorship_export_assets", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)


class AdminSponsorshipAddViewTests(SponsorshipReviewTestBase):
    def test_add_view_renders(self):
        admin = get_user_model().objects.create_superuser("root", "root@example.com", "pass")
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("admin:sponsors_sponsorship_add")).status_code, 200)
