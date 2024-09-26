from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Subquery
from django.urls import reverse, reverse_lazy
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    CreateView, DetailView, TemplateView, UpdateView, DeleteView, ListView, FormView
)

from allauth.account.views import SignupView, PasswordChangeView
from honeypot.decorators import check_honeypot

from pydotorg.mixins import LoginRequiredMixin
from sponsors.forms import SponsorUpdateForm, SponsorRequiredAssetsForm
from sponsors.models import Sponsor, BenefitFeature

from .forms import (
    UserProfileForm, MembershipForm, MembershipUpdateForm,
)
from .models import Membership
from sponsors.models import Sponsorship

User = get_user_model()


class MembershipCreate(LoginRequiredMixin, CreateView):
    model = Membership
    form_class = MembershipForm
    template_name = 'users/membership_form.html'

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated and self.request.user.has_membership:
            return redirect('users:user_membership_edit')
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'email_address': self.request.user.email}
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()

        # Send subscription email to mailing lists
        if settings.MAILING_LIST_PSF_MEMBERS and self.object.psf_announcements:
            send_mail(
                subject='PSF Members Announce Signup from python.org',
                message='subscribe',
                from_email=self.object.creator.email,
                recipient_list=[settings.MAILING_LIST_PSF_MEMBERS],
            )

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('users:user_membership_thanks')


class MembershipUpdate(LoginRequiredMixin, UpdateView):
    form_class = MembershipUpdateForm
    template_name = 'users/membership_form.html'

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_object(self):
        if self.request.user.has_membership:
            return self.request.user.membership
        else:
            raise Http404()

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('users:user_membership_thanks')


class MembershipThanks(TemplateView):
    template_name = 'users/membership_thanks.html'


class MembershipVoteAffirm(TemplateView):
    template_name = 'users/membership_vote_affirm.html'

    def post(self, request, *args, **kwargs):
        """ Store the vote affirmation """
        self.request.user.membership.votes = True
        self.request.user.membership.last_vote_affirmation = timezone.now()
        self.request.user.membership.save()
        return redirect('users:membership_affirm_vote_done')


class MembershipVoteAffirmDone(TemplateView):
    template_name = 'users/membership_vote_affirm_done.html'


class UserUpdate(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm
    slug_field = 'username'
    template_name = 'users/user_form.html'

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return User.objects.get(username=self.request.user)


class UserDetail(DetailView):
    slug_field = 'username'

    def get_queryset(self):
        queryset = User.objects.select_related()
        if self.request.user.username == self.kwargs['slug']:
            return queryset
        return queryset.searchable()


class HoneypotSignupView(SignupView):

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    # Add honeypot support to 'password change' form and
    # redirect it to the user editing form.

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('users:user_profile_edit')


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    success_url = reverse_lazy('home')
    slug_field = 'username'
    raise_exception = True
    http_method_names = ['post', 'delete']

    def test_func(self):
        return self.get_object() == self.request.user


class MembershipDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Membership
    slug_field = 'creator__username'
    raise_exception = True
    http_method_names = ['post', 'delete']

    def get_success_url(self):
        return reverse('users:user_detail', kwargs={'slug': self.request.user.username})

    def test_func(self):
        return self.get_object().creator == self.request.user


class UserNominationsView(LoginRequiredMixin, TemplateView):
    model = User
    template_name = 'users/nominations_view.html'

    def get_queryset(self):
        return User.objects.select_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        elections = defaultdict(lambda: {'nominations_recieved': [], 'nominations_made': []})
        for nomination in self.request.user.nominations_recieved.all():
            nominations = nomination.nominations.all()
            for nomin in nominations:
                nomin.is_editable = nomin.editable(user=self.request.user)
                elections[nomination.election]['nominations_recieved'].append(nomin)
        for nomination in self.request.user.nominations_made.all():
            nomination.is_editable = nomination.editable(user=self.request.user)
            elections[nomination.election]['nominations_made'].append(nomination)
        context['elections'] = dict(sorted(dict(elections).items(), key=lambda item: item[0].date, reverse=True))
        return context


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class UserSponsorshipsDashboard(ListView):
    context_object_name = 'sponsorships'
    template_name = 'users/list_user_sponsorships.html'

    def get_queryset(self):
        return self.request.user.sponsorships.select_related("sponsor")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        sponsorships = context["sponsorships"]
        context["active"] = [sp for sp in sponsorships if sp.is_active]

        by_status = []
        inactive = [sp for sp in sponsorships if not sp.is_active]
        for value, label in Sponsorship.STATUS_CHOICES[::-1]:
            by_status.append((
                label, [
                    sp for sp in inactive
                    if sp.status == value
                ]
            ))

        context["by_status"] = by_status
        return context


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class SponsorshipDetailView(DetailView):
    context_object_name = 'sponsorship'
    template_name = 'users/sponsorship_detail.html'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Sponsorship.objects.select_related("sponsor").all()
        return self.request.user.sponsorships.select_related("sponsor")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        sponsorship = context["sponsorship"]
        required_assets = BenefitFeature.objects.required_assets().from_sponsorship(sponsorship)
        fulfilled, pending = [], []
        for asset in required_assets:
            if bool(asset.value):
                fulfilled.append(asset)
            else:
                pending.append(asset)

        provided_assets = BenefitFeature.objects.provided_assets().from_sponsorship(sponsorship)
        provided = []
        for asset in provided_assets:
            if bool(asset.value):
                provided.append(asset)

        context["required_assets"] = pending
        context["fulfilled_assets"] = fulfilled
        context["provided_assets"] = provided
        context["sponsor"] = sponsorship.sponsor
        return context


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class UpdateSponsorInfoView(UpdateView):
    object_name = "sponsor"
    template_name = 'sponsors/new_sponsorship_application_form.html'
    form_class = SponsorUpdateForm

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Sponsor.objects.all()
        sponsor_ids = self.request.user.sponsorships.values_list("sponsor_id", flat=True)
        return Sponsor.objects.filter(id__in=Subquery(sponsor_ids))

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Sponsor info updated with success.")
        return self.request.path

@login_required(login_url=settings.LOGIN_URL)
def edit_sponsor_info_implicit(request):
    sponsors = Sponsor.objects.filter(contacts__user=request.user).all()
    if len(sponsors) == 0:
        messages.add_message(request, messages.INFO, "No Sponsors associated with your user.")
        return redirect('users:user_profile_edit')
    elif len(sponsors) == 1:
        return redirect('users:edit_sponsor_info', pk=sponsors[0].id)
    else:
        messages.add_message(request, messages.INFO, "Multiple Sponsors associated with your user.")
        return render(request, 'users/sponsor_select.html', context={"sponsors": sponsors})


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class UpdateSponsorshipAssetsView(UpdateView):
    object_name = "sponsorship"
    template_name = 'users/sponsorship_assets_update.html'
    form_class = SponsorRequiredAssetsForm

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Sponsorship.objects.select_related("sponsor").all()
        return self.request.user.sponsorships.select_related("sponsor")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        specific_asset = self.request.GET.get("required_asset", None)
        if specific_asset:
            kwargs["required_assets_ids"] = [specific_asset]
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["required_asset_id"] = self.request.GET.get("required_asset", None)
        return context

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Assets were updated with success.")
        return reverse("users:sponsorship_application_detail", args=[self.object.pk])

    def form_valid(self, form):
        form.update_assets()
        return redirect(self.get_success_url())


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class ProvidedSponsorshipAssetsView(DetailView):
    """TODO: Deprecate this view now that everything lives in the SponsorshipDetailView"""
    object_name = "sponsorship"
    template_name = 'users/sponsorship_assets_view.html'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Sponsorship.objects.select_related("sponsor").all()
        return self.request.user.sponsorships.select_related("sponsor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provided_assets = BenefitFeature.objects.provided_assets().from_sponsorship(context["sponsorship"])
        provided = []
        for asset in provided_assets:
            if bool(asset.value):
                provided.append(asset)
        context["provided_assets"] = provided
        context["provided_asset_id"] = self.request.GET.get("provided_asset", None)
        return context
