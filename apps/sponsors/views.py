"""Public-facing views for the sponsorship application workflow."""

from itertools import chain
from pathlib import PurePosixPath

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.forms.utils import ErrorList
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.sponsors import cookies, use_cases
from apps.sponsors.forms import SponsorshipApplicationForm, SponsorshipsBenefitsForm
from apps.sponsors.models import (
    Contract,
    FileAsset,
    ProvidedFileAsset,
    ProvidedFileAssetConfiguration,
    Sponsor,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
)

# Each tracked benefit file field, with the sponsors models whose view/change permission lets staff download it.
SPONSOR_ASSET_FILE_SOURCES = (
    (FileAsset, "file", ("genericasset", "fileasset")),
    (ProvidedFileAssetConfiguration, "shared_file", ("providedfileassetconfiguration",)),
    (ProvidedFileAsset, "shared_file", ("providedfileasset",)),
)


class SelectSponsorshipApplicationBenefitsView(FormView):
    """View for selecting sponsorship package and benefits before applying."""

    form_class = SponsorshipsBenefitsForm
    template_name = "sponsors/sponsorship_benefits_form.html"

    def get_context_data(self, *args, **kwargs):
        """Add benefit programs, packages, and capacity info to the context."""
        programs = SponsorshipProgram.objects.all()
        packages = SponsorshipPackage.objects.all()
        benefits_qs = SponsorshipBenefit.objects.select_related("program")
        capacities_met = any(any(not b.has_capacity for b in benefits_qs.filter(program=p)) for p in programs)
        kwargs.update(
            {
                "benefit_model": SponsorshipBenefit,
                "sponsorship_packages": packages,
                "capacities_met": capacities_met,
                "custom_year": self.get_form_custom_year(),
            }
        )
        return super().get_context_data(*args, **kwargs)

    def get_success_url(self):
        """Return the URL for the sponsorship application form, with login redirect if needed."""
        if self.request.user.is_authenticated:
            return reverse_lazy("new_sponsorship_application")
        return f"{settings.LOGIN_URL}?next={reverse('new_sponsorship_application')}"

    def get_initial(self):
        """Load previously selected benefits from the cookie."""
        return cookies.get_sponsorship_selected_benefits(self.request)

    def get_form_kwargs(self):
        """Add custom year to form kwargs if configured by staff."""
        kwargs = super().get_form_kwargs()
        custom_year = self.get_form_custom_year()
        if custom_year:
            kwargs["year"] = custom_year
        return kwargs

    def get_form_custom_year(self):
        """Return a custom configuration year if the staff user specifies one via query param."""
        custom_year = self.request.GET.get("config_year")
        if self.request.user.is_staff and custom_year:
            custom_year = int(custom_year)
            if custom_year != SponsorshipCurrentYear.get_year():
                return custom_year
        return None

    def form_valid(self, form):
        """Validate the cookie and store selected benefits for the next step."""
        if not self.request.session.test_cookie_worked():
            error = ErrorList()
            error.append("You must allow cookies from python.org to proceed.")
            form._errors.setdefault("__all__", error)  # noqa: SLF001 - Django form internal API for adding non-field errors
            return self.form_invalid(form)

        response = super().form_valid(form)
        self._set_form_data_cookie(form, response)
        return response

    def get(self, request, *args, **kwargs):
        """Set a test cookie and render the benefits selection form."""
        request.session.set_test_cookie()
        return super().get(request, *args, **kwargs)

    def _set_form_data_cookie(self, form, response):
        pkg = form.cleaned_data.get("package", "")
        data = {
            "package": "" if not pkg else pkg.id,
        }
        for fname, benefits in [
            (f, v)
            for f, v in form.cleaned_data.items()
            if f.startswith("benefits_") or f in ["a_la_carte_benefits", "standalone_benefits"]
        ]:
            data[fname] = sorted(b.id for b in benefits)

        cookies.set_sponsorship_selected_benefits(response, data)


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class NewSponsorshipApplicationView(FormView):
    """View for submitting a new sponsorship application with sponsor details."""

    form_class = SponsorshipApplicationForm
    template_name = "sponsors/new_sponsorship_application_form.html"

    def _redirect_back_to_benefits(self):
        msg = "You have to select sponsorship package and benefits before."
        messages.add_message(self.request, messages.INFO, msg)
        return redirect(reverse("select_sponsorship_application_benefits"))

    @property
    def benefits_data(self):
        """Return the selected benefits data stored in the cookie."""
        return cookies.get_sponsorship_selected_benefits(self.request)

    def get(self, *args, **kwargs):
        """Redirect to benefits selection if no benefits have been chosen yet."""
        if not self.benefits_data:
            return self._redirect_back_to_benefits()
        return super().get(*args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        """Add the current user to the form kwargs."""
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, *args, **kwargs):
        """Add package, benefits, and pricing information to the template context."""
        package_id = self.benefits_data.get("package")
        package = None if not package_id else SponsorshipPackage.objects.get(id=package_id)
        benefits_ids = chain(*(self.benefits_data[k] for k in self.benefits_data if k != "package"))
        benefits = SponsorshipBenefit.objects.filter(id__in=benefits_ids)

        # sponsorship benefits holds selected package's benefits
        # added benefits holds holds extra benefits added by users
        added_benefits, sponsorship_benefits = [], benefits
        price = None
        if package and not package.has_user_customization(benefits):
            price = package.sponsorship_amount
        elif package:
            sponsorship_benefits = []
            package_benefits = package.benefits.all()
            for benefit in benefits:
                if benefit in package_benefits:
                    sponsorship_benefits.append(benefit)
                else:
                    added_benefits.append(benefit)
        else:
            added_benefits, sponsorship_benefits = sponsorship_benefits, []

        kwargs.update(
            {
                "sponsorship_package": package,
                "sponsorship_benefits": sponsorship_benefits,
                "added_benefits": added_benefits,
                "sponsorship_price": price,
            }
        )
        return super().get_context_data(*args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        """Create the sponsor and sponsorship application, then clear the cookie."""
        benefits_form = SponsorshipsBenefitsForm(data=self.benefits_data)
        if not benefits_form.is_valid():
            return self._redirect_back_to_benefits()

        sponsor = form.save()

        uc = use_cases.CreateSponsorshipApplicationUseCase.build()
        sponsorship = uc.execute(
            self.request.user,
            sponsor,
            benefits_form.get_benefits(include_a_la_carte=True, include_standalone=True),
            benefits_form.get_package(),
            request=self.request,
        )
        notified = uc.notifications[1].get_recipient_list({"user": self.request.user, "sponsorship": sponsorship})

        response = render(
            self.request,
            "sponsors/sponsorship_application_finished.html",
            context={"sponsorship": sponsorship, "notified": notified},
        )
        cookies.delete_sponsorship_selected_benefits(response)
        return response


def _is_sponsorship_manager(user, *model_names):
    """Allow active sponsorship managers and staff who may view or change one of the named sponsors models."""
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser or user.groups.filter(name="Sponsorship Admin").exists():
        return True
    return user.is_staff and any(
        user.has_perm(f"sponsors.{action}_{model_name}") for model_name in model_names for action in ("view", "change")
    )


def _private_attachment(field_file, name):
    """Stream a private file as an uncached attachment, or 404 when storage no longer has it."""
    try:
        document = field_file.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc

    response = FileResponse(
        document,
        content_type="application/octet-stream",
        as_attachment=True,
        filename=PurePosixPath(name).name,
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def download_contract_document(request, name):
    """Authorize each request before streaming an exact, tracked contract attachment."""
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not _is_sponsorship_manager(request.user, "contract"):
        raise PermissionDenied

    contract = Contract.objects.filter(Q(document=name) | Q(document_docx=name) | Q(signed_document=name)).first()
    if contract is None:
        raise Http404

    field_file = next(
        f for f in (contract.document, contract.document_docx, contract.signed_document) if f.name == name
    )
    return _private_attachment(field_file, name)


def _api_token_or_session_user(request):
    """Return the user of a sent API token, like the sponsors API, falling back to the session user."""
    try:
        authenticated = TokenAuthentication().authenticate(request)
    except AuthenticationFailed as exc:
        raise PermissionDenied from exc
    return authenticated[0] if authenticated else request.user


def _tracked_sponsor_asset(name):
    """Return the field file tracked under ``name`` and the sponsors models governing staff access to it."""
    field_file, model_names = None, ["sponsorship"]
    for model, field, governing_models in SPONSOR_ASSET_FILE_SOURCES:
        record = model.objects.filter(**{field: name}).first()
        if record is not None:
            field_file = field_file or getattr(record, field)
            model_names.extend(governing_models)
    if field_file is None:
        return None, ()
    return field_file, model_names


def _sponsor_can_view_asset(user, name):
    """Return whether ``name`` belongs to a sponsorship, or the sponsor of one, that the user can see."""
    visible = Sponsorship.objects.visible_to(user)
    visible_ids = visible.values("pk")
    content_types = ContentType.objects.get_for_models(Sponsor, Sponsorship)
    owned_upload = Q(content_type=content_types[Sponsorship], object_id__in=visible_ids) | Q(
        content_type=content_types[Sponsor], object_id__in=visible.values("sponsor_id")
    )
    return (
        FileAsset.objects.filter(owned_upload, file=name).exists()
        or ProvidedFileAsset.objects.filter(shared_file=name, sponsor_benefit__sponsorship__in=visible_ids).exists()
    )


def download_sponsor_asset(request, name):
    """Authorize each request before streaming a tracked provided or uploaded benefit file.

    Sponsorship managers, sponsor publishers (API token or session) and portal users who can see an owning
    sponsorship may download. Untracked names are 404 only for users who could otherwise download any file.
    """
    user = _api_token_or_session_user(request)
    if not user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    field_file, model_names = _tracked_sponsor_asset(name)
    allowed = (
        (user.is_active and user.has_perm("sponsors.sponsor_publisher"))
        or _is_sponsorship_manager(user, *model_names)
        or _sponsor_can_view_asset(user, name)
    )
    if not allowed:
        raise PermissionDenied
    if field_file is None:
        raise Http404
    return _private_attachment(field_file, name)
