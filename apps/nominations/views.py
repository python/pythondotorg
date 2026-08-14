"""Views for browsing elections, nominees, and managing nominations."""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.nominations.forms import (
    BoardNominationCreateForm,
    NominationAcceptForm,
    NominationForm,
    PackagingCouncilNominationCreateForm,
)
from apps.nominations.models import Election, ElectionKind, Nomination, Nominee
from pydotorg.mixins import LoginRequiredMixin


class ElectionsList(ListView):
    """List all PSF board elections."""

    model = Election


class ElectionDetail(DetailView):
    """Display details for a single election."""

    def get(self, request, *args, **kwargs):
        """Handle GET request for election detail."""
        self.object = self.get_object()
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_object(self):
        """Look up the election by slug from the URL, 404ing on an unknown slug."""
        election = get_object_or_404(Election, slug=self.kwargs["election"])
        self.election = election
        return election

    def get_context_data(self, **kwargs):
        """Return context with the election object."""
        return {"election": self.election}


class NominationMixin:
    """Mixin that injects the current election into the template context."""

    @cached_property
    def election(self):
        """Return the election named by the URL slug, 404ing on an unknown slug."""
        return get_object_or_404(Election.objects.select_related("kind"), slug=self.kwargs["election"])

    def get_context_data(self, **kwargs):
        """Add the election from the URL slug to the context."""
        context = super().get_context_data(**kwargs)
        context["election"] = self.election
        return context


class NomineeList(NominationMixin, ListView):
    """List nominees for a given election."""

    template_name = "nominations/nominee_list.html"

    def get_queryset(self, *args, **kwargs):
        """Return visible nominees based on election status and user permissions."""
        election = self.election
        if election.nominations_complete or self.request.user.is_superuser:
            return Nominee.objects.filter(accepted=True, approved=True, election=election).exclude(user=None)

        if self.request.user.is_authenticated:
            # Before the results are public, preview the nominees relevant to
            # this user in this election: the people they nominated, plus
            # themselves when somebody nominated them.
            return (
                Nominee.objects.filter(
                    Q(user=self.request.user) | Q(nominations__nominator=self.request.user),
                    election=election,
                )
                .exclude(user=None)
                .distinct()
                .select_related("user")
            )
        return None


class NomineeDetail(NominationMixin, DetailView):
    """Display details for a single nominee."""

    def get(self, request, *args, **kwargs):
        """Handle GET request, raising 404 if nominee is not visible."""
        self.object = self.get_object()
        if not self.object.visible(user=request.user):
            raise Http404

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        """Return nominees for the election specified in the URL."""
        return Nominee.objects.filter(election=self.election).select_related()

    def get_context_data(self, **kwargs):
        """Return context data for the nominee detail page."""
        return super().get_context_data(**kwargs)


class NominationCreate(LoginRequiredMixin, NominationMixin, CreateView):
    """Create a new nomination for a board election."""

    model = Nomination

    login_message = "Please login to make a nomination."

    form_classes = {
        ElectionKind.NominationFormVariant.BOARD: BoardNominationCreateForm,
        ElectionKind.NominationFormVariant.PACKAGING_COUNCIL: PackagingCouncilNominationCreateForm,
    }

    def get_form_kwargs(self):
        """Add the request and election to the form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs.update({"request": self.request, "election": self.election})
        return kwargs

    def get_form_class(self):
        """Return the form class for the election's kind, 404ing when nominations are not open."""
        election = self.election
        if election.nominations_complete:
            messages.error(self.request, f"Nominations for {election.name} Election are closed")
            msg = f"Nominations for {election.name} Election are closed"
            raise Http404(msg)
        if not election.nominations_open:
            messages.error(self.request, f"Nominations for {election.name} Election are not open")
            msg = f"Nominations for {election.name} Election are not open"
            raise Http404(msg)

        return self.form_classes[election.nomination_form_variant]

    def get_success_url(self):
        """Return the URL for the newly created nomination detail page."""
        return reverse(
            "nominations:nomination_detail",
            kwargs={"election": self.object.election.slug, "pk": self.object.id},
        )

    def form_valid(self, form):
        """Set nominator, election, and handle self-nomination before saving."""
        form.instance.nominator = self.request.user
        form.instance.election = self.election
        if form.cleaned_data.get("self_nomination", False):
            try:
                nominee = Nominee.objects.get(user=self.request.user, election=form.instance.election)
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
        """Return context data for the nomination creation page."""
        return super().get_context_data(**kwargs)


class NominationEdit(LoginRequiredMixin, NominationMixin, UserPassesTestMixin, UpdateView):
    """Edit an existing nomination."""

    model = Nomination
    form_class = NominationForm
    # Give authenticated non-owners a 403 instead of a login redirect loop.
    raise_exception = True

    def test_func(self):
        """Allow editing only while the nomination is still editable."""
        return self.get_object().editable(self.request.user)

    def get_queryset(self):
        """Fetch the nomination for the URL's election with its kind in one query."""
        return Nomination.objects.filter(election__slug=self.kwargs["election"]).select_related("election__kind")

    def get_form_kwargs(self):
        """Pass the nomination's election so the form can theme its fields."""
        kwargs = super().get_form_kwargs()
        kwargs["election"] = self.object.election
        return kwargs

    def get_success_url(self):
        """Return the next URL from POST data or the nomination detail page."""
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url

        if self.object.pk:
            return reverse(
                "nominations:nomination_detail",
                kwargs={"election": self.object.election.slug, "pk": self.object.id},
            )

        return super().get_success_url()

    def get_context_data(self, **kwargs):
        """Return context data for the nomination edit page."""
        return super().get_context_data(**kwargs)


class NominationAccept(LoginRequiredMixin, NominationMixin, UserPassesTestMixin, UpdateView):
    """Accept or decline a nomination."""

    model = Nomination
    form_class = NominationAcceptForm
    template_name_suffix = "_accept_form"
    # Give authenticated non-owners a 403 instead of a login redirect loop.
    raise_exception = True

    def test_func(self):
        """Only allow the nominee to accept while nominations are open."""
        nomination = self.get_object()
        return self.request.user == nomination.nominee.user and nomination.election.nominations_open

    def get_queryset(self):
        """Fetch the URL election's nomination with the related objects the template renders."""
        return Nomination.objects.filter(election__slug=self.kwargs["election"]).select_related(
            "election__kind", "nominee__user", "nominator"
        )

    def get_success_url(self):
        """Return the next URL from POST data or the nomination detail page."""
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url

        if self.object.pk:
            return reverse(
                "nominations:nomination_detail",
                kwargs={"election": self.object.election.slug, "pk": self.object.id},
            )

        return super().get_success_url()

    def get_context_data(self, **kwargs):
        """Return context data for the nomination accept page."""
        return super().get_context_data(**kwargs)


class NominationStatementPreview(LoginRequiredMixin, View):
    """Render a nomination statement preview using the model field's own pipeline."""

    def post(self, request):
        """Return the statement rendered exactly as it will be stored."""
        return JsonResponse({"html": Nomination.render_statement(request.POST.get("text", ""))})


class NominationView(DetailView):
    """Display details for a single nomination."""

    def get(self, request, *args, **kwargs):
        """Handle GET request, raising 404 if nomination is not visible."""
        self.object = self.get_object()
        if not self.object.visible(user=request.user):
            raise Http404

        context = self.get_context_data(object=self.object)
        context["editable"] = self.object.editable(user=self.request.user)
        return self.render_to_response(context)

    def get_queryset(self):
        """Return the URL election's nominations with related objects."""
        return Nomination.objects.filter(election__slug=self.kwargs["election"]).select_related(
            "election__kind", "nominee__user", "nominator"
        )

    def get_context_data(self, **kwargs):
        """Return context data for the nomination detail page."""
        return super().get_context_data(**kwargs)
