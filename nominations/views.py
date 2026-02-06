from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from pydotorg.mixins import GroupRequiredMixin, LoginRequiredMixin

from nominations.forms import (
    FellowNominationForm,
    FellowNominationManageForm,
    FellowNominationRoundForm,
    FellowNominationStatusForm,
    FellowNominationVoteForm,
    NominationAcceptForm,
    NominationCreateForm,
    NominationForm,
)
from nominations.models import (
    Election,
    Fellow,
    FellowNomination,
    FellowNominationRound,
    FellowNominationVote,
    Nomination,
    Nominee,
)
from nominations.notifications import (
    FellowNominationAcceptedNotification,
    FellowNominationNotAcceptedNotification,
    FellowNominationSubmittedToNominator,
    FellowNominationSubmittedToWG,
)


class ElectionsList(ListView):
    model = Election


class ElectionDetail(DetailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_object(self):
        election = Election.objects.get(slug=self.kwargs["election"])
        self.election = election
        return election

    def get_context_data(self, **kwargs):
        context = {"election": self.election}
        return context


class NominationMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.election = Election.objects.get(slug=self.kwargs["election"])
        context["election"] = self.election
        return context


class NomineeList(NominationMixin, ListView):
    template_name = "nominations/nominee_list.html"

    def get_queryset(self, *args, **kwargs):
        election = Election.objects.get(slug=self.kwargs["election"])
        if election.nominations_complete or self.request.user.is_superuser:
            return Nominee.objects.filter(
                accepted=True, approved=True, election=election
            ).exclude(user=None)

        elif self.request.user.is_authenticated:
            return Nominee.objects.filter(user=self.request.user)


class NomineeDetail(NominationMixin, DetailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.visible(user=request.user):
            raise Http404

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        election = Election.objects.get(slug=self.kwargs["election"])
        queryset = Nominee.objects.filter(election=election).select_related()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NominationCreate(LoginRequiredMixin, NominationMixin, CreateView):
    model = Nomination

    login_message = "Please login to make a nomination."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"request": self.request})
        return kwargs

    def get_form_class(self):
        election = Election.objects.get(slug=self.kwargs["election"])
        if election.nominations_complete:
            messages.error(
                self.request, f"Nominations for {election.name} Election are closed"
            )
            raise Http404(f"Nominations for {election.name} Election are closed")
        if not election.nominations_open:
            messages.error(
                self.request, f"Nominations for {election.name} Election are not open"
            )
            raise Http404(f"Nominations for {election.name} Election are not open")

        return NominationCreateForm

    def get_success_url(self):
        return reverse(
            "nominations:nomination_detail",
            kwargs={"election": self.object.election.slug, "pk": self.object.id},
        )

    def form_valid(self, form):
        form.instance.nominator = self.request.user
        form.instance.election = Election.objects.get(slug=self.kwargs["election"])
        if form.cleaned_data.get("self_nomination", False):
            try:
                nominee = Nominee.objects.get(
                    user=self.request.user, election=form.instance.election
                )
            except Nominee.DoesNotExist:
                nominee = Nominee.objects.create(
                    user=self.request.user,
                    election=form.instance.election,
                    accepted=True,
                )
            form.instance.nominee = nominee
            form.instance.accepted = True
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NominationEdit(LoginRequiredMixin, NominationMixin, UserPassesTestMixin, UpdateView):
    model = Nomination
    form_class = NominationForm

    def test_func(self):
        return self.request.user == self.get_object().nominator

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url

        elif self.object.pk:
            return reverse(
                "nominations:nomination_detail",
                kwargs={"election": self.object.election.slug, "pk": self.object.id},
            )

        else:
            return super().get_success_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NominationAccept(LoginRequiredMixin, NominationMixin, UserPassesTestMixin, UpdateView):
    model = Nomination
    form_class = NominationAcceptForm
    template_name_suffix = '_accept_form'

    def test_func(self):
        return self.request.user == self.get_object().nominee.user

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url

        elif self.object.pk:
            return reverse(
                "nominations:nomination_detail",
                kwargs={"election": self.object.election.slug, "pk": self.object.id},
            )

        else:
            return super().get_success_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NominationView(DetailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.visible(user=request.user):
            raise Http404

        context = self.get_context_data(object=self.object)
        context["editable"] = self.object.editable(user=self.request.user)
        return self.render_to_response(context)

    def get_queryset(self):
        queryset = Nomination.objects.select_related()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


# --- Fellow Nomination Views ---


class FellowWGRequiredMixin(GroupRequiredMixin):
    """Restrict access to PSF Fellow Work Group members (and staff)."""

    group_required = "PSF Fellow Work Group"
    raise_exception = True

    def check_membership(self, group):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        return super().check_membership(group)


class FellowNominationCreate(LoginRequiredMixin, CreateView):
    """Submit a new PSF Fellow nomination."""

    model = FellowNomination
    form_class = FellowNominationForm
    template_name = "nominations/fellow_nomination_form.html"
    login_message = "Please login to submit a Fellow nomination."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_round = FellowNominationRound.objects.filter(is_open=True).first()
        if current_round is None or not current_round.is_accepting_nominations:
            raise Http404("Fellow nominations are not currently open.")
        context["nomination_round"] = current_round
        return context

    def form_valid(self, form):
        current_round = FellowNominationRound.objects.filter(is_open=True).first()
        if current_round is None or not current_round.is_accepting_nominations:
            raise Http404("Fellow nominations are not currently open.")

        form.instance.nominator = self.request.user
        form.instance.nomination_round = current_round

        # Compute expiry round (4 quarters later = current quarter + 3)
        expiry_year = current_round.year
        expiry_quarter = current_round.quarter + 3
        if expiry_quarter > 4:
            expiry_year += (expiry_quarter - 1) // 4
            expiry_quarter = ((expiry_quarter - 1) % 4) + 1
        form.instance.expiry_round = FellowNominationRound.objects.filter(
            year=expiry_year, quarter=expiry_quarter
        ).first()

        # Cross-reference nominee_email against User table
        from users.models import User
        nominee_email = form.cleaned_data["nominee_email"]
        try:
            nominee_user = User.objects.get(email__iexact=nominee_email)
            form.instance.nominee_user = nominee_user
            # Check if nominee is already a Fellow
            try:
                if nominee_user.fellow is not None:
                    form.instance.nominee_is_fellow_at_submission = True
                    messages.warning(
                        self.request,
                        f"{form.cleaned_data['nominee_name']} is already a PSF Fellow. "
                        "The nomination has been saved but may not need further action.",
                    )
            except Fellow.DoesNotExist:
                pass
        except User.DoesNotExist:
            pass

        response = super().form_valid(form)

        # Send email notifications
        FellowNominationSubmittedToNominator().notify(
            nomination=self.object, request=self.request
        )
        FellowNominationSubmittedToWG().notify(
            nomination=self.object, request=self.request
        )

        messages.success(
            self.request,
            "Your Fellow nomination has been submitted successfully. "
            "You can track its status on your nominations page.",
        )
        return response

    def get_success_url(self):
        return reverse("nominations:fellow_my_nominations")


class FellowNominationDetail(LoginRequiredMixin, DetailView):
    """View details of a Fellow nomination."""

    model = FellowNomination
    template_name = "nominations/fellow_nomination_detail.html"
    context_object_name = "nomination"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Visible to: nominator, staff, superuser, PSF Fellow Work Group members
        if user == obj.nominator or user.is_staff or user.is_superuser:
            return obj
        if user.groups.filter(name="PSF Fellow Work Group").exists():
            return obj
        raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        in_wg_group = user.groups.filter(name="PSF Fellow Work Group").exists()
        is_wg_member = in_wg_group or user.is_staff or user.is_superuser
        context["is_wg_member"] = is_wg_member

        if is_wg_member:
            nomination = self.object
            votes = nomination.votes.select_related("voter").all()
            context["votes"] = votes
            context["user_vote"] = nomination.votes.filter(voter=user).first()
            context["vote_result"] = nomination.vote_result
            context["yes_count"] = votes.filter(vote="yes").count()
            context["no_count"] = votes.filter(vote="no").count()
            context["abstain_count"] = votes.filter(vote="abstain").count()

        return context


class MyFellowNominations(LoginRequiredMixin, ListView):
    """List the current user's Fellow nominations."""

    template_name = "nominations/fellow_my_nominations.html"
    context_object_name = "nominations"

    def get_queryset(self):
        return FellowNomination.objects.filter(
            nominator=self.request.user
        ).select_related("nomination_round", "expiry_round")


# --- Fellow WG Management Views ---


class FellowNominationDashboard(LoginRequiredMixin, FellowWGRequiredMixin, TemplateView):
    """Dashboard overview for PSF Fellow Work Group members."""

    template_name = "nominations/fellow_nomination_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_round = FellowNominationRound.objects.filter(is_open=True).first()
        context["current_round"] = current_round

        if current_round:
            round_nominations = FellowNomination.objects.filter(
                nomination_round=current_round
            )
            context["total_nominations"] = round_nominations.count()
            context["pending_count"] = round_nominations.filter(
                status=FellowNomination.PENDING
            ).count()
            context["under_review_count"] = round_nominations.filter(
                status=FellowNomination.UNDER_REVIEW
            ).count()
            context["accepted_count"] = round_nominations.filter(
                status=FellowNomination.ACCEPTED
            ).count()
            context["not_accepted_count"] = round_nominations.filter(
                status=FellowNomination.NOT_ACCEPTED
            ).count()
            needs_your_vote = round_nominations.filter(
                status=FellowNomination.UNDER_REVIEW
            ).exclude(
                votes__voter=self.request.user
            )
            context["needs_votes_count"] = needs_your_vote.count()
            context["needs_votes_nominations"] = needs_your_vote.select_related(
                "nomination_round"
            )

        context["recent_rounds"] = FellowNominationRound.objects.all()[:4]
        return context


class FellowNominationReview(LoginRequiredMixin, FellowWGRequiredMixin, ListView):
    """Review list of Fellow nominations for WG members."""

    template_name = "nominations/fellow_nomination_review.html"
    context_object_name = "nominations"

    def get_queryset(self):
        view_mode = self.request.GET.get("view", "active")
        round_slug = self.request.GET.get("round")

        if view_mode == "all":
            qs = FellowNomination.objects.all()
        else:
            qs = FellowNomination.objects.active()

        if round_slug:
            qs = qs.filter(nomination_round__slug=round_slug)

        return qs.select_related(
            "nomination_round", "nominator"
        ).annotate(
            yes_count=Count("votes", filter=Q(votes__vote="yes")),
            no_count=Count("votes", filter=Q(votes__vote="no")),
            abstain_count=Count("votes", filter=Q(votes__vote="abstain")),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rounds"] = FellowNominationRound.objects.all()
        context["current_view"] = self.request.GET.get("view", "active")
        context["selected_round"] = self.request.GET.get("round", "")
        return context


class FellowNominationStatusUpdate(LoginRequiredMixin, FellowWGRequiredMixin, UpdateView):
    """Update the status of a Fellow nomination."""

    model = FellowNomination
    form_class = FellowNominationStatusForm
    template_name = "nominations/fellow_nomination_status_form.html"

    def form_valid(self, form):
        old_status = FellowNomination.objects.filter(pk=self.object.pk).values_list(
            "status", flat=True
        ).first()
        form.instance.last_modified_by = self.request.user
        response = super().form_valid(form)

        new_status = self.object.status
        if old_status != new_status:
            messages.success(
                self.request,
                f"Status updated to '{self.object.get_status_display()}' for {self.object.nominee_name}.",
            )
            if new_status == FellowNomination.ACCEPTED:
                FellowNominationAcceptedNotification().notify(
                    nomination=self.object, request=self.request
                )
            elif new_status == FellowNomination.NOT_ACCEPTED:
                FellowNominationNotAcceptedNotification().notify(
                    nomination=self.object, request=self.request
                )
        else:
            messages.info(self.request, "No status change was made.")

        return response

    def get_success_url(self):
        return reverse(
            "nominations:fellow_nomination_detail", kwargs={"pk": self.object.pk}
        )


class FellowNominationVoteView(LoginRequiredMixin, FellowWGRequiredMixin, CreateView):
    """Cast a vote on a Fellow nomination."""

    model = FellowNominationVote
    form_class = FellowNominationVoteForm
    template_name = "nominations/fellow_nomination_vote_form.html"

    def get_nomination(self):
        return get_object_or_404(FellowNomination, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nomination"] = self.get_nomination()
        return context

    def form_valid(self, form):
        nomination = self.get_nomination()
        if nomination.status != FellowNomination.UNDER_REVIEW:
            messages.error(
                self.request,
                "Votes can only be cast on nominations that are under review.",
            )
            return redirect(
                "nominations:fellow_nomination_detail", pk=nomination.pk
            )
        form.instance.voter = self.request.user
        form.instance.nomination = nomination
        try:
            with transaction.atomic():
                response = super().form_valid(form)
            messages.success(
                self.request,
                f"Your vote on {nomination.nominee_name} has been recorded.",
            )
            return response
        except IntegrityError:
            messages.error(
                self.request,
                "You have already voted on this nomination.",
            )
            return redirect(
                "nominations:fellow_nomination_detail", pk=nomination.pk
            )

    def get_success_url(self):
        return reverse(
            "nominations:fellow_nomination_detail",
            kwargs={"pk": self.object.nomination.pk},
        )


class FellowNominationRoundList(LoginRequiredMixin, FellowWGRequiredMixin, ListView):
    """List all Fellow nomination rounds."""

    model = FellowNominationRound
    template_name = "nominations/fellow_round_list.html"
    context_object_name = "rounds"

    def get_queryset(self):
        return FellowNominationRound.objects.annotate(
            nomination_count=Count("nominations")
        )


class FellowNominationRoundCreate(LoginRequiredMixin, FellowWGRequiredMixin, CreateView):
    """Create a new Fellow nomination round."""

    model = FellowNominationRound
    form_class = FellowNominationRoundForm
    template_name = "nominations/fellow_round_form.html"

    def get_success_url(self):
        return reverse("nominations:fellow_round_list")


class FellowNominationRoundUpdate(LoginRequiredMixin, FellowWGRequiredMixin, UpdateView):
    """Edit an existing Fellow nomination round."""

    model = FellowNominationRound
    form_class = FellowNominationRoundForm
    template_name = "nominations/fellow_round_form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_success_url(self):
        return reverse("nominations:fellow_round_list")


class FellowNominationRoundToggle(LoginRequiredMixin, FellowWGRequiredMixin, View):
    """Toggle the is_open flag on a Fellow nomination round (POST only)."""

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])

    def post(self, request, *args, **kwargs):
        nomination_round = get_object_or_404(
            FellowNominationRound, slug=kwargs["slug"]
        )
        nomination_round.is_open = not nomination_round.is_open
        nomination_round.save()
        return redirect("nominations:fellow_round_list")


class FellowNominationEdit(LoginRequiredMixin, FellowWGRequiredMixin, UpdateView):
    """Full edit form for WG members to manage a Fellow nomination."""

    model = FellowNomination
    form_class = FellowNominationManageForm
    template_name = "nominations/fellow_nomination_manage_form.html"

    def form_valid(self, form):
        form.instance.last_modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nomination"] = self.object
        return context

    def get_success_url(self):
        return reverse(
            "nominations:fellow_nomination_detail", kwargs={"pk": self.object.pk}
        )


class FellowNominationDelete(LoginRequiredMixin, FellowWGRequiredMixin, DeleteView):
    """Delete a Fellow nomination (WG only)."""

    model = FellowNomination
    template_name = "nominations/fellow_nomination_confirm_delete.html"

    def get_success_url(self):
        return reverse("nominations:fellow_nomination_review")


# --- Fellows Roster (Public) ---


class FellowsRoster(ListView):
    """Public roster of PSF Fellows."""

    template_name = "nominations/fellows_roster.html"
    context_object_name = "fellows"

    def get_queryset(self):
        return Fellow.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = context["fellows"]
        context["active_fellows"] = qs.filter(status=Fellow.ACTIVE)
        context["emeritus_fellows"] = qs.filter(status=Fellow.EMERITUS)
        context["deceased_fellows"] = qs.filter(status=Fellow.DECEASED)
        context["active_count"] = context["active_fellows"].count()
        context["emeritus_count"] = context["emeritus_fellows"].count()
        context["deceased_count"] = context["deceased_fellows"].count()
        context["total_count"] = qs.count()
        context["years"] = (
            Fellow.objects.values_list("year_elected", flat=True)
            .distinct()
            .order_by("-year_elected")
        )
        return context