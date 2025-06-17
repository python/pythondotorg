from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker

from django.conf import settings
from django.test import TestCase

from sponsors.forms import (
    SponsorshipsBenefitsForm,
    SponsorshipApplicationForm,
    Sponsor,
    SponsorContactForm,
    SponsorContactFormSet,
    SponsorBenefitAdminInlineForm,
    SponsorBenefit,
    Sponsorship,
    SponsorshipsListForm,
    SendSponsorshipNotificationForm, SponsorRequiredAssetsForm, SponsorshipBenefitAdminForm, CloneApplicationConfigForm,
)
from sponsors.models import SponsorshipBenefit, SponsorContact, RequiredTextAssetConfiguration, \
    RequiredImgAssetConfiguration, ImgAsset, RequiredTextAsset, SponsorshipPackage, SponsorshipCurrentYear
from .utils import get_static_image_file_as_upload
from ..models.enums import AssetsRelatedTo


class SponsorshipsBenefitsFormTests(TestCase):
    def setUp(self):
        self.current_year = SponsorshipCurrentYear.get_year()
        self.psf = baker.make("sponsors.SponsorshipProgram", name="PSF")
        self.wk = baker.make("sponsors.SponsorshipProgram", name="Working Group")
        self.program_1_benefits = baker.make(
            SponsorshipBenefit, program=self.psf, _quantity=3, year=self.current_year
        )
        self.program_2_benefits = baker.make(
            SponsorshipBenefit, program=self.wk, _quantity=5, year=self.current_year
        )
        self.package = baker.make(
            "sponsors.SponsorshipPackage", advertise=True, year=self.current_year
        )
        self.package.benefits.add(*self.program_1_benefits)
        self.package.benefits.add(*self.program_2_benefits)

        # packages without associated packages
        self.a_la_carte = baker.make(
            SponsorshipBenefit, program=self.psf, _quantity=2, year=self.current_year
        )

        # standalone benefits
        self.standalone = baker.make(
            SponsorshipBenefit, program=self.psf, standalone=True, _quantity=2, year=self.current_year
        )

    def test_specific_field_to_select_a_la_carte_by_year(self):
        prev_year = self.current_year - 1
        from_prev_year = baker.make(
            SponsorshipBenefit, program=self.psf, _quantity=2, year=prev_year
        )
        # current year by default
        form = SponsorshipsBenefitsForm()
        choices = list(form.fields["a_la_carte_benefits"].choices)
        self.assertEqual(len(self.a_la_carte), len(choices))
        for benefit in self.a_la_carte:
            self.assertIn(benefit.id, [c[0] for c in choices])

        form = SponsorshipsBenefitsForm(year=prev_year)
        choices = list(form.fields["a_la_carte_benefits"].choices)
        self.assertEqual(len(self.a_la_carte), len(choices))
        for benefit in from_prev_year:
            self.assertIn(benefit.id, [c[0] for c in choices])

    def test_benefits_from_current_year_organized_by_program(self):
        older_psf = baker.make(
            SponsorshipBenefit, program=self.psf, _quantity=3, year=self.current_year - 1
        )
        older_wk = baker.make(
            SponsorshipBenefit, program=self.wk, _quantity=5, year=self.current_year - 1
        )
        self.package.benefits.add(*older_psf)
        self.package.benefits.add(*older_wk)

        form = SponsorshipsBenefitsForm()
        field1, field2 = sorted(form.benefits_programs, key=lambda f: f.name)

        self.assertEqual("benefits_psf", field1.name)
        self.assertEqual("PSF Benefits", field1.label)
        choices = list(field1.field.choices)
        self.assertEqual(len(self.program_1_benefits), len(choices))
        for benefit in self.program_1_benefits:
            self.assertIn(benefit.id, [c[0] for c in choices])

        self.assertEqual("benefits_working_group", field2.name)
        self.assertEqual("Working Group Benefits", field2.label)
        choices = list(field2.field.choices)
        self.assertEqual(len(self.program_2_benefits), len(choices))
        for benefit in self.program_2_benefits:
            self.assertIn(benefit.id, [c[0] for c in choices])

    def test_specific_field_to_select_standalone_benefits_by_year(self):
        prev_year = self.current_year - 1
        # standalone benefits
        prev_benefits = baker.make(
            SponsorshipBenefit, program=self.psf, standalone=True, _quantity=2, year=prev_year
        )

        # Current year by default
        form = SponsorshipsBenefitsForm()
        choices = list(form.fields["standalone_benefits"].choices)
        self.assertEqual(len(self.standalone), len(choices))
        for benefit in self.standalone:
            self.assertIn(benefit.id, [c[0] for c in choices])

        # Current year by default
        form = SponsorshipsBenefitsForm(year=prev_year)
        choices = list(form.fields["standalone_benefits"].choices)
        self.assertEqual(len(self.standalone), len(choices))
        for benefit in prev_benefits:
            self.assertIn(benefit.id, [c[0] for c in choices])

    def test_package_list_only_advertisable_ones_from_current_year(self):
        ads_pkgs = baker.make(
            'SponsorshipPackage', advertise=True, _quantity=2, year=self.current_year
        )
        baker.make('SponsorshipPackage', advertise=False)
        baker.make('SponsorshipPackage', advertise=False, year=self.current_year)

        form = SponsorshipsBenefitsForm()
        field = form.fields.get("package")

        self.assertEqual(3, field.queryset.count())

    def test_invalidate_form_without_benefits(self):
        form = SponsorshipsBenefitsForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

        form = SponsorshipsBenefitsForm(
            data={"benefits_psf": [self.program_1_benefits[0].id], "package": self.package.id}
        )
        self.assertTrue(form.is_valid())

    def test_validate_form_without_package_but_with_standalone_benefits(self):
        benefit = self.standalone[0]
        form = SponsorshipsBenefitsForm(
            data={"standalone_benefits": [benefit.id]}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual([], form.get_benefits())
        self.assertEqual([benefit], form.get_benefits(include_standalone=True))

    def test_do_not_validate_form_with_package_and_standalone_benefits(self):
        benefit = self.standalone[0]
        data = {
            "standalone_benefits": [benefit.id],
            "package": self.package.id,
            "benefits_psf": [self.program_1_benefits[0].id],
        }
        form = SponsorshipsBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Application with package cannot have standalone benefits.",
            form.errors["__all__"]
        )

    def test_should_not_validate_form_without_package_with_a_la_carte_benefits(self):
        data = {
            "a_la_carte_benefits": [self.a_la_carte[0].id],
        }

        form = SponsorshipsBenefitsForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "You must pick a package to include the selected benefits.",
            form.errors["__all__"]
        )

        data.update({
            "package": self.package.id,
        })
        form = SponsorshipsBenefitsForm(data=data)
        self.assertTrue(form.is_valid())

    def test_do_not_validate_package_package_with_disabled_a_la_carte_benefits(self):
        self.package.allow_a_la_carte = False
        self.package.save()
        data = {
            "package": self.package.id,
            "benefits_psf": [self.program_1_benefits[0].id],
            "a_la_carte_benefits": [self.a_la_carte[0].id],
        }
        form = SponsorshipsBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Package does not accept a la carte benefits.",
            form.errors["__all__"]
        )
        data.pop("a_la_carte_benefits")
        form = SponsorshipsBenefitsForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_benefits_conflicts_helper_property(self):
        benefit_1, benefit_2 = baker.make("sponsors.SponsorshipBenefit", _quantity=2)
        benefit_1.conflicts.add(*self.program_1_benefits)
        benefit_2.conflicts.add(*self.program_2_benefits)

        form = SponsorshipsBenefitsForm()
        map = form.benefits_conflicts

        # conflicts are symmetrical relationships
        self.assertEqual(
            2 + len(self.program_1_benefits) + len(self.program_2_benefits), len(map)
        )
        self.assertEqual(
            sorted(map[benefit_1.id]), sorted(b.id for b in self.program_1_benefits)
        )
        self.assertEqual(
            sorted(map[benefit_2.id]), sorted(b.id for b in self.program_2_benefits)
        )
        for b in self.program_1_benefits:
            self.assertEqual(map[b.id], [benefit_1.id])
        for b in self.program_2_benefits:
            self.assertEqual(map[b.id], [benefit_2.id])

    def test_invalid_form_if_any_conflict(self):
        benefit_1 = baker.make("sponsors.SponsorshipBenefit", program=self.wk, year=self.current_year)
        benefit_1.conflicts.add(*self.program_1_benefits)
        self.package.benefits.add(benefit_1)

        data = {"benefits_psf": [b.id for b in self.program_1_benefits], "package": self.package.id}
        form = SponsorshipsBenefitsForm(data=data)
        self.assertTrue(form.is_valid())

        data["benefits_working_group"] = [benefit_1.id]
        form = SponsorshipsBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "The application has 1 or more benefits that conflicts.",
            form.errors["__all__"],
        )

    def test_get_benefits_from_cleaned_data(self):
        benefit = self.program_1_benefits[0]

        data = {"benefits_psf": [benefit.id],
                "a_la_carte_benefits": [b.id for b in self.a_la_carte],
                "package": self.package.id}
        form = SponsorshipsBenefitsForm(data=data)
        self.assertTrue(form.is_valid())

        benefits = form.get_benefits()
        self.assertEqual(1, len(benefits))
        self.assertIn(benefit, benefits)

        benefits = form.get_benefits(include_a_la_carte=True)
        self.assertEqual(3, len(benefits))
        self.assertIn(benefit, benefits)
        for a_la_carte in self.a_la_carte:
            self.assertIn(a_la_carte, benefits)

    def test_package_only_benefit_without_package_should_not_validate(self):
        SponsorshipBenefit.objects.all().update(package_only=True)

        data = {"benefits_psf": [self.program_1_benefits[0]]}

        form = SponsorshipsBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "You must pick a package to include the selected benefits.",
            form.errors["__all__"],
        )

    def test_package_only_benefit_with_wrong_package_should_not_validate(self):
        SponsorshipBenefit.objects.all().update(package_only=True)
        package = baker.make("sponsors.SponsorshipPackage", advertise=True, year=self.current_year)
        package.benefits.add(*SponsorshipBenefit.objects.all())

        data = {
            "benefits_psf": [self.program_1_benefits[0]],
            "package": baker.make("sponsors.SponsorshipPackage", advertise=True, year=self.current_year).id,  # other package
        }

        form = SponsorshipsBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "The application has 1 or more package only benefits but wrong sponsor package.",
            form.errors["__all__"][0],
        )

        data = {
            "benefits_psf": [self.program_1_benefits[0]],
            "package": package.id,
        }
        form = SponsorshipsBenefitsForm(data=data)
        self.assertTrue(form.is_valid())

    def test_benefit_with_no_capacity_should_not_validate(self):
        SponsorshipBenefit.objects.all().update(capacity=0)

        data = {"benefits_psf": [self.program_1_benefits[0]], "package": self.package.id}

        form = SponsorshipsBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "The application has 1 or more benefits with no capacity.",
            form.errors["__all__"],
        )

    def test_benefit_with_soft_capacity_should_validate(self):
        SponsorshipBenefit.objects.all().update(capacity=0, soft_capacity=True)

        data = {"benefits_psf": [self.program_1_benefits[0]], "package": self.package.id}

        form = SponsorshipsBenefitsForm(data=data)
        self.assertTrue(form.is_valid())

    def test_get_package_return_selected_package(self):
        data = {"benefits_psf": [self.program_1_benefits[0]], "package": self.package.id}
        form = SponsorshipsBenefitsForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(self.package, form.get_package())

    def test_get_package_get_or_create_standalone_only_package(self):
        data = {"standalone_benefits": [self.standalone[0].id]}
        form = SponsorshipsBenefitsForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(1, SponsorshipPackage.objects.count())

        # should create package if it doesn't exist yet
        package = form.get_package()
        self.assertEqual("Standalone Only", package.name)
        self.assertEqual("standalone-only", package.slug)
        self.assertEqual(175, package.logo_dimension)
        self.assertEqual(0, package.sponsorship_amount)
        self.assertFalse(package.advertise)
        self.assertEqual(2, SponsorshipPackage.objects.count())

        # re-use previously created package for subsequent applications
        data = {"standalone_benefits": [self.standalone[0].id]}
        form = SponsorshipsBenefitsForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(package, form.get_package())
        self.assertEqual(2, SponsorshipPackage.objects.count())


class SponsorshipApplicationFormTests(TestCase):
    def setUp(self):
        self.data = {
            "name": "CompanyX",
            "primary_phone": "+14141413131",
            "mailing_address_line_1": "4th street",
            "mailing_address_line_2": "424",
            "city": "New York",
            "state": "NY",
            "postal_code": "10212",
            "country": "US",
            "contact-0-name": "Bernardo",
            "contact-0-email": "bernardo@companyemail.com",
            "contact-0-phone": "+1999999999",
            "contact-0-primary": True,
            "contact-TOTAL_FORMS": 1,
            "contact-MAX_NUM_FORMS": 5,
            "contact-MIN_NUM_FORMS": 1,
            "contact-INITIAL_FORMS": 1,
        }
        self.files = {
            "web_logo": get_static_image_file_as_upload("psf-logo.png", "logo.png")
        }

    def test_required_fields(self):
        required_fields = [
            "name",
            "web_logo",
            "primary_phone",
            "mailing_address_line_1",
            "city",
            "postal_code",
            "country",
            "__all__",
        ]

        form = SponsorshipApplicationForm(
            {
                "contact-TOTAL_FORMS": 0,
                "contact-MAX_NUM_FORMS": 5,
                "contact-MIN_NUM_FORMS": 1,
                "contact-INITIAL_FORMS": 1,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(len(required_fields), len(form.errors), msg=form.errors)
        for required in required_fields:
            self.assertIn(required, form.errors)

    def test_create_sponsor_with_valid_data(self):
        user = baker.make(settings.AUTH_USER_MODEL)
        form = SponsorshipApplicationForm(self.data, self.files, user=user)
        self.assertTrue(form.is_valid(), form.errors)

        sponsor = form.save()

        self.assertTrue(sponsor.pk)
        self.assertEqual(sponsor.name, "CompanyX")
        self.assertTrue(sponsor.web_logo)
        self.assertEqual(sponsor.primary_phone, "+14141413131")
        self.assertEqual(sponsor.mailing_address_line_1, "4th street")
        self.assertEqual(sponsor.mailing_address_line_2, "424")
        self.assertEqual(sponsor.city, "New York")
        self.assertEqual(sponsor.state, "NY")
        self.assertEqual(sponsor.postal_code, "10212")
        self.assertEqual(sponsor.country, "US")
        self.assertEqual(sponsor.country.name, "United States of America")
        self.assertEqual(sponsor.description, "")
        self.assertIsNone(sponsor.print_logo.name)
        self.assertEqual(sponsor.landing_page_url, "")
        contact = sponsor.contacts.get()
        self.assertEqual(contact.name, "Bernardo")
        self.assertEqual(contact.email, "bernardo@companyemail.com")
        self.assertEqual(contact.phone, "+1999999999")
        self.assertIsNone(contact.user)

    def test_create_sponsor_with_valid_data_for_non_required_inputs(
            self,
    ):
        user = baker.make(settings.AUTH_USER_MODEL)

        self.data["description"] = "Important company"
        self.data["landing_page_url"] = "https://companyx.com"
        self.data["twitter_handle"] = "@companyx"
        self.data["country_of_incorporation"] = "US"
        self.data["state_of_incorporation"] = "NY"
        self.files["print_logo"] = get_static_image_file_as_upload(
            "psf-logo_print.png", "logo_print.png"
        )

        form = SponsorshipApplicationForm(self.data, self.files, user=user)
        self.assertTrue(form.is_valid(), form.errors)

        sponsor = form.save()

        self.assertEqual(sponsor.description, "Important company")
        self.assertTrue(sponsor.print_logo)
        self.assertFalse(form.user_with_previous_sponsors)
        self.assertEqual(sponsor.landing_page_url, "https://companyx.com")
        self.assertEqual(sponsor.twitter_handle, "@companyx")
        self.assertEqual(sponsor.country_of_incorporation, "US")
        self.assertEqual(sponsor.state_of_incorporation, "NY")

    def test_create_sponsor_with_svg_for_print_logo(
            self,
    ):
        tick_svg = Path(settings.STATICFILES_DIRS[0]) / "img"/"sponsors"/"tick.svg"
        with tick_svg.open("rb") as fd:
            uploaded_svg = SimpleUploadedFile("tick.svg", fd.read())
        self.files["print_logo"] = uploaded_svg

        form = SponsorshipApplicationForm(self.data, self.files)
        self.assertTrue(form.is_valid(), form.errors)

        sponsor = form.save()

        self.assertTrue(sponsor.print_logo)

    def test_use_previous_user_sponsor(self):
        contact = baker.make(SponsorContact, user__email="foo@foo.com")
        self.data = {"sponsor": contact.sponsor.id}

        form = SponsorshipApplicationForm(self.data, self.files, user=contact.user)
        self.assertTrue(form.is_valid(), form.errors)

        saved_sponsor = form.save()
        self.assertTrue(form.user_with_previous_sponsors)
        self.assertEqual(saved_sponsor, contact.sponsor)
        self.assertEqual(Sponsor.objects.count(), 1)
        self.assertEqual(saved_sponsor.contacts.get(), contact)

    def test_invalidate_form_if_user_selects_sponsort_from_other_user(self):
        contact = baker.make(SponsorContact, user__email="foo@foo.com")
        self.data = {"sponsor": contact.sponsor.id}
        other_user = baker.make(settings.AUTH_USER_MODEL)

        form = SponsorshipApplicationForm(self.data, self.files, user=other_user)

        self.assertFalse(form.is_valid())
        self.assertFalse(form.user_with_previous_sponsors)
        self.assertIn("sponsor", form.errors)
        self.assertEqual(1, len(form.errors))

    def test_invalidate_form_if_sponsor_with_sponsorships(self):
        contact = baker.make(SponsorContact, user__email="foo@foo.com")
        self.data = {"sponsor": contact.sponsor.id}

        prev_sponsorship = baker.make("sponsors.Sponsorship", sponsor=contact.sponsor)
        form = SponsorshipApplicationForm(self.data, self.files, user=contact.user)
        self.assertFalse(form.is_valid())
        self.assertIn("sponsor", form.errors)

        prev_sponsorship.status = prev_sponsorship.FINALIZED
        prev_sponsorship.save()
        form = SponsorshipApplicationForm(self.data, self.files, user=contact.user)
        self.assertTrue(form.is_valid())

    def test_create_multiple_contacts_and_user_contact(self):
        user_email = "secondary@companyemail.com"
        self.data.update(
            {
                "contact-1-name": "Secondary",
                "contact-1-email": user_email,
                "contact-1-phone": "+1123123123",
                "contact-TOTAL_FORMS": 2,
            }
        )
        user = baker.make(settings.AUTH_USER_MODEL, email=user_email.upper())
        form = SponsorshipApplicationForm(self.data, self.files, user=user)
        self.assertTrue(form.is_valid(), form.errors)

        sponsor = form.save()

        self.assertEqual(2, sponsor.contacts.count())
        c1, c2 = sorted(sponsor.contacts.all(), key=lambda c: c.name)
        self.assertEqual(c1.name, "Bernardo")
        self.assertTrue(c1.primary)  # first contact should be the primary one
        self.assertIsNone(c1.user)
        self.assertEqual(c2.name, "Secondary")
        self.assertFalse(c2.primary)
        self.assertEqual(c2.user, user)

    def test_invalidate_form_if_no_primary_contact(self):
        self.data.pop("contact-0-primary")
        user = baker.make(settings.AUTH_USER_MODEL)
        form = SponsorshipApplicationForm(self.data, self.files, user=user)
        self.assertFalse(form.is_valid())
        msg = "You have to mark at least one contact as the primary one."
        self.assertIn(msg, form.errors["__all__"])

    def test_initial_primary_contact(self):
        form = SponsorshipApplicationForm()
        formset = form.contacts_formset

        self.assertTrue(
            formset.forms[0].initial.get("primary"),
            "The primary field in the first contact form should be initially set to True."
        )


class SponsorContactFormSetTests(TestCase):
    def setUp(self):
        self.data = {
            "contact-TOTAL_FORMS": 0,
            "contact-MAX_NUM_FORMS": 5,
            "contact-MIN_NUM_FORMS": 1,
            "contact-INITIAL_FORMS": 1,
        }

    def test_contact_formset(self):
        sponsor = baker.make(Sponsor)
        self.data.update(
            {
                "contact-0-name": "Bernardo",
                "contact-0-email": "bernardo@companyemail.com",
                "contact-0-phone": "+1999999999",
                "contact-1-name": "Foo",
                "contact-1-email": "foo@bar.com",
                "contact-1-phone": "+1111111111",
                "contact-TOTAL_FORMS": 2,
            }
        )

        formset = SponsorContactFormSet(self.data, prefix="contact")
        self.assertTrue(formset.is_valid())
        for form in formset.forms:
            contact = form.save(commit=False)
            contact.sponsor = sponsor
            contact.save()

        self.assertEqual(2, SponsorContact.objects.count())

    def test_invalidate_formset_if_no_form(self):
        self.data["contact-TOTAL_FORMS"] = 0
        formset = SponsorContactFormSet(self.data, prefix="contact")
        self.assertFalse(formset.is_valid())


class SponsorBenefitAdminInlineFormTests(TestCase):
    def setUp(self):
        self.benefit = baker.make(SponsorshipBenefit)
        self.sponsorship = baker.make(Sponsorship)
        self.data = {
            "sponsorship_benefit": self.benefit.pk,
            "sponsorship": self.sponsorship.pk,
            "benefit_internal_value": 200,
        }

    def test_required_fields_for_new_sponsor_benefit(self):
        required_fields = [
            "sponsorship",
        ]

        form = SponsorBenefitAdminInlineForm({})
        self.assertFalse(form.is_valid())

        for required in required_fields:
            self.assertIn(required, form.errors)
        self.assertEqual(len(required_fields), len(form.errors))

    def test_create_new_sponsor_benefit_for_sponsorship(self):
        form = SponsorBenefitAdminInlineForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        sponsor_benefit = form.save()
        sponsor_benefit.refresh_from_db()

        self.assertEqual(sponsor_benefit.sponsorship, self.sponsorship)
        self.assertEqual(sponsor_benefit.sponsorship_benefit, self.benefit)
        self.assertEqual(sponsor_benefit.name, self.benefit.name)
        self.assertEqual(sponsor_benefit.description, self.benefit.description)
        self.assertEqual(sponsor_benefit.program, self.benefit.program)
        self.assertEqual(sponsor_benefit.benefit_internal_value, 200)

    def test_update_existing_sponsor_benefit(self):
        sponsor_benefit = baker.make(
            SponsorBenefit,
            sponsorship=self.sponsorship,
            sponsorship_benefit=self.benefit,
        )
        new_benefit = baker.make(SponsorshipBenefit, standalone=True)
        self.data["sponsorship_benefit"] = new_benefit.pk

        form = SponsorBenefitAdminInlineForm(data=self.data, instance=sponsor_benefit)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        sponsor_benefit.refresh_from_db()

        self.assertEqual(1, SponsorBenefit.objects.count())
        self.assertEqual(sponsor_benefit.sponsorship, self.sponsorship)
        self.assertEqual(sponsor_benefit.sponsorship_benefit, new_benefit)
        self.assertEqual(sponsor_benefit.name, new_benefit.name)
        self.assertEqual(sponsor_benefit.description, new_benefit.description)
        self.assertEqual(sponsor_benefit.program, new_benefit.program)
        self.assertEqual(sponsor_benefit.benefit_internal_value, 200)
        self.assertTrue(sponsor_benefit.added_by_user)
        self.assertTrue(sponsor_benefit.standalone)

    def test_do_not_update_sponsorship_if_it_doesn_change(self):
        sponsor_benefit = baker.make(
            SponsorBenefit,
            sponsorship=self.sponsorship,
            sponsorship_benefit=self.benefit,
        )

        form = SponsorBenefitAdminInlineForm(data=self.data, instance=sponsor_benefit)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        sponsor_benefit.refresh_from_db()
        self.benefit.name = "new name"
        self.benefit.save()

        self.assertEqual(1, SponsorBenefit.objects.count())
        self.assertEqual(sponsor_benefit.sponsorship, self.sponsorship)
        self.assertEqual(sponsor_benefit.sponsorship_benefit, self.benefit)
        self.assertNotEqual(sponsor_benefit.name, "new name")
        self.assertEqual(sponsor_benefit.benefit_internal_value, 200)

    def test_update_existing_benefit_features(self):
        sponsor_benefit = baker.make(
            SponsorBenefit,
            sponsorship=self.sponsorship,
            sponsorship_benefit=self.benefit,
        )
        # existing benefit depends on logo
        baker.make_recipe('sponsors.tests.logo_at_download_feature', sponsor_benefit=sponsor_benefit)

        # new benefit requires text instead of logo
        new_benefit = baker.make(SponsorshipBenefit)
        baker.make(RequiredTextAssetConfiguration, benefit=new_benefit, internal_name='foo',
                   related_to=AssetsRelatedTo.SPONSORSHIP.value)
        self.data["sponsorship_benefit"] = new_benefit.pk

        form = SponsorBenefitAdminInlineForm(data=self.data, instance=sponsor_benefit)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        sponsor_benefit.refresh_from_db()

        self.assertEqual(sponsor_benefit.features.count(), 1)
        self.assertIsInstance(sponsor_benefit.features.get(), RequiredTextAsset)


class SponsorshipsFormTestCase(TestCase):

    def test_list_all_sponsorships_as_choices_by_default(self):
        sponsorships = baker.make(Sponsorship, _quantity=3)

        form = SponsorshipsListForm()
        qs = form.fields["sponsorships"].queryset

        self.assertEqual(3, qs.count())
        for sponsorship in sponsorships:
            self.assertIn(sponsorship, qs)

    def test_init_form_from_sponsorship_benefit(self):
        benefit = baker.make(SponsorshipBenefit)
        sponsor_benefit = baker.make(SponsorBenefit, sponsorship_benefit=benefit)
        other_benefit = baker.make(SponsorshipBenefit)
        baker.make(SponsorBenefit, sponsorship_benefit=other_benefit)

        form = SponsorshipsListForm.with_benefit(benefit)

        with self.assertNumQueries(1):
            qs = list(form.fields["sponsorships"].queryset)

        self.assertEqual(1, len(qs))
        self.assertIn(sponsor_benefit.sponsorship, qs)
        self.assertEqual(benefit, form.sponsorship_benefit)


class SponsorContactFormTests(TestCase):

    def test_ensure_model_form_configuration(self):
        expected_fields = ["name", "email", "phone", "primary", "administrative", "accounting"]
        meta = SponsorContactForm._meta
        self.assertEqual(set(expected_fields), set(meta.fields))
        self.assertEqual(SponsorContact, meta.model)


class SendSponsorshipNotificationFormTests(TestCase):

    def setUp(self):
        self.notification = baker.make("sponsors.SponsorEmailNotificationTemplate")
        self.data = {
            "notification": self.notification.pk,
            "contact_types": [SponsorContact.MANAGER_CONTACT, SponsorContact.ADMINISTRATIVE_CONTACT],
        }

    def test_required_fields(self):
        required_fields = set(["__all__", "contact_types"])
        form = SendSponsorshipNotificationForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual(required_fields, set(form.errors))

    def test_get_contact_types_list(self):
        form = SendSponsorshipNotificationForm(self.data)
        self.assertTrue(form.is_valid())
        self.assertEqual(self.data["contact_types"], form.cleaned_data["contact_types"])
        self.assertEqual(self.notification, form.get_notification())

    def test_form_error_if_notification_and_email_custom_content(self):
        self.data["content"] = "email content"
        form = SendSponsorshipNotificationForm(self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_form_error_if_not_notification_and_neither_custom_content(self):
        self.data.pop("notification")
        form = SendSponsorshipNotificationForm(self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_validate_form_with_custom_content(self):
        self.data.pop("notification")
        self.data.update({"content": "content", "subject": "subject"})
        form = SendSponsorshipNotificationForm(self.data)
        self.assertTrue(form.is_valid())
        notification = form.get_notification()
        self.assertEqual("content", notification.content)
        self.assertEqual("subject", notification.subject)
        self.assertIsNone(notification.pk)


class SponsorRequiredAssetsFormTest(TestCase):

    def setUp(self):
        self.sponsorship = baker.make(Sponsorship, sponsor__name="foo")
        self.required_text_cfg = baker.make(
            RequiredTextAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSORSHIP.value,
            internal_name="Text Input",
            _fill_optional=True,
        )
        self.required_img_cfg = baker.make(
            RequiredImgAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSOR.value,
            internal_name="Image Input",
            _fill_optional=True,
        )
        self.benefits = baker.make(
            SponsorBenefit, sponsorship=self.sponsorship, _quantity=3
        )

    def test_build_form_with_no_fields_if_no_required_asset(self):
        form = SponsorRequiredAssetsForm(instance=self.sponsorship)
        self.assertEqual(len(form.fields), 0)
        self.assertFalse(form.has_input)

    def test_build_form_fields_from_required_assets(self):
        text_asset = self.required_text_cfg.create_benefit_feature(self.benefits[0])
        img_asset = self.required_img_cfg.create_benefit_feature(self.benefits[1])

        form = SponsorRequiredAssetsForm(instance=self.sponsorship)
        fields = dict(form.fields)

        self.assertEqual(len(fields), 2)
        self.assertEqual(type(text_asset.as_form_field()), type(fields["text_input"]))
        self.assertEqual(type(img_asset.as_form_field()), type(fields["image_input"]))
        self.assertTrue(form.has_input)

    def test_build_form_fields_from_specific_list_of_required_assets(self):
        text_asset = self.required_text_cfg.create_benefit_feature(self.benefits[0])
        img_asset = self.required_img_cfg.create_benefit_feature(self.benefits[1])

        form = SponsorRequiredAssetsForm(instance=self.sponsorship, required_assets_ids=[text_asset.pk])
        fields = dict(form.fields)

        self.assertEqual(len(fields), 1)
        self.assertEqual(type(text_asset.as_form_field()), type(fields["text_input"]))

    def test_save_info_for_text_asset(self):
        text_asset = self.required_text_cfg.create_benefit_feature(self.benefits[0])
        data = {"text_input": "submitted data"}

        form = SponsorRequiredAssetsForm(instance=self.sponsorship, data=data)
        self.assertTrue(form.is_valid())
        form.update_assets()

        self.assertEqual("submitted data", text_asset.value)

    def test_save_info_for_image_asset(self):
        img_asset = self.required_img_cfg.create_benefit_feature(self.benefits[0])
        files = {"image_input": get_static_image_file_as_upload("psf-logo.png", "logo.png")}

        form = SponsorRequiredAssetsForm(instance=self.sponsorship, data={}, files=files)
        self.assertTrue(form.is_valid())
        form.update_assets()
        asset = ImgAsset.objects.get()
        expected_url = f"/media/sponsors-app-assets/{asset.uuid}.png"

        self.assertEqual(expected_url, img_asset.value.url)

    def test_load_initial_from_assets_and_force_field_if_previous_Data(self):
        img_asset = self.required_img_cfg.create_benefit_feature(self.benefits[0])
        text_asset = self.required_text_cfg.create_benefit_feature(self.benefits[0])
        files = {"image_input": get_static_image_file_as_upload("psf-logo.png", "logo.png")}
        form = SponsorRequiredAssetsForm(instance=self.sponsorship, data={"text_input": "data"}, files=files)
        self.assertTrue(form.is_valid())
        form.update_assets()

        form = SponsorRequiredAssetsForm(instance=self.sponsorship, data={}, files=files)
        self.assertTrue(form.fields["image_input"].initial)
        self.assertTrue(form.fields["text_input"].initial)
        self.assertTrue(form.fields["text_input"].required)
        self.assertTrue(form.fields["image_input"].required)

    def test_raise_error_if_form_initialized_without_instance(self):
        self.assertRaises(TypeError, SponsorRequiredAssetsForm)


class SponsorshipBenefitAdminFormTests(TestCase):

    def setUp(self):
        self.program = baker.make("sponsors.SponsorshipProgram")

    def test_required_fields(self):
        required = {"name", "program", "year"}
        form = SponsorshipBenefitAdminForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), required)

    def test_standalone_benefit_cannot_have_package(self):
        data = {"name": "benefit", "program": self.program.pk, "standalone": True, "year": 2023}
        form = SponsorshipBenefitAdminForm(data=data)
        self.assertTrue(form.is_valid())

        package = baker.make("sponsors.SponsorshipPackage")
        data["packages"] = [package.pk]
        form = SponsorshipBenefitAdminForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class CloneApplicationConfigFormTests(TestCase):

    def setUp(self):
        baker.make(SponsorshipBenefit, year=2022)
        baker.make(SponsorshipPackage, year=2023)

    def test_required_fields(self):
        req_fields = {"from_year", "target_year"}
        form = CloneApplicationConfigForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(req_fields, set(form.errors))

    def test_from_year_should_list_configured_years_as_possible_choices(self):
        expected = [(2023, 2023), (2022, 2022)]
        form = CloneApplicationConfigForm()
        from_years = form.fields["from_year"].choices
        self.assertEqual(expected, from_years)
        self.assertEqual([2023, 2022], form.configured_years)

    def test_target_must_be_greater_than_from_year(self):
        # lower
        data = {"from_year": 2023, "target_year": 2020}
        form = CloneApplicationConfigForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        # greater
        data = {"from_year": 2023, "target_year": 2024}
        form = CloneApplicationConfigForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(2023, form.cleaned_data["from_year"])
        self.assertEqual(2024, form.cleaned_data["target_year"])

    def test_target_cannot_be_an_already_configured_year(self):
        # the same
        data = {"from_year": 2022, "target_year": 2023}
        form = CloneApplicationConfigForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_target_year_has_2050_as_an_upper_boundary(self):
        data = {"from_year": 2023, "target_year": 2050}
        form = CloneApplicationConfigForm(data=data)
        self.assertTrue(form.is_valid())

        data = {"from_year": 2023, "target_year": 2051}
        form = CloneApplicationConfigForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("target_year", form.errors)
