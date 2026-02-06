"""Views for browsing elections, nominees, and managing nominations."""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from nominations.forms import NominationAcceptForm, NominationCreateForm, NominationForm
from nominations.models import Election, Nomination, Nominee
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
        """Look up the election by slug from the URL."""
        election = Election.objects.get(slug=self.kwargs["election"])
        self.election = election
        return election

    def get_context_data(self, **kwargs):
        """Return context with the election object."""
        return {"election": self.election}


class NominationMixin:
    """Mixin that injects the current election into the template context."""

    def get_context_data(self, **kwargs):
        """Add the election from the URL slug to the context."""
        context = super().get_context_data(**kwargs)
        self.election = Election.objects.get(slug=self.kwargs["election"])
        context["election"] = self.election
        return context


class NomineeList(NominationMixin, ListView):
    """List nominees for a given election."""

    template_name = "nominations/nominee_list.html"

    def get_queryset(self, *args, **kwargs):
        """Return visible nominees based on election status and user permissions."""
        election = Election.objects.get(slug=self.kwargs["election"])
        if election.nominations_complete or self.request.user.is_superuser:
            return Nominee.objects.filter(accepted=True, approved=True, election=election).exclude(user=None)

        if self.request.user.is_authenticated:
            return Nominee.objects.filter(user=self.request.user)
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
        election = Election.objects.get(slug=self.kwargs["election"])
        return Nominee.objects.filter(election=election).select_related()

    def get_context_data(self, **kwargs):
        """Return context data for the nominee detail page."""
        return super().get_context_data(**kwargs)


class NominationCreate(LoginRequiredMixin, NominationMixin, CreateView):
    """Create a new nomination for a board election."""

    model = Nomination

    login_message = "Please login to make a nomination."

    def get_form_kwargs(self):
        """Add the request to the form kwargs for self-nomination validation."""
        kwargs = super().get_form_kwargs()
        kwargs.update({"request": self.request})
        return kwargs

    def get_form_class(self):
        """Return the form class, raising 404 if nominations are closed or not open."""
        election = Election.objects.get(slug=self.kwargs["election"])
        if election.nominations_complete:
            messages.error(self.request, f"Nominations for {election.name} Election are closed")
            msg = f"Nominations for {election.name} Election are closed"
            raise Http404(msg)
        if not election.nominations_open:
            messages.error(self.request, f"Nominations for {election.name} Election are not open")
            msg = f"Nominations for {election.name} Election are not open"
            raise Http404(msg)

        return NominationCreateForm

    def get_success_url(self):
        """Return the URL for the newly created nomination detail page."""
        return reverse(
            "nominations:nomination_detail",
            kwargs={"election": self.object.election.slug, "pk": self.object.id},
        )

    def form_valid(self, form):
        """Set nominator, election, and handle self-nomination before saving."""
        form.instance.nominator = self.request.user
        form.instance.election = Election.objects.get(slug=self.kwargs["election"])
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

    def test_func(self):
        """Only allow the original nominator to edit."""
        return self.request.user == self.get_object().nominator

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

    def test_func(self):
        """Only allow the nominee to accept."""
        return self.request.user == self.get_object().nominee.user

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
        """Return all nominations with related objects."""
        return Nomination.objects.select_related()

    def get_context_data(self, **kwargs):
        """Return context data for the nomination detail page."""
        return super().get_context_data(**kwargs)
