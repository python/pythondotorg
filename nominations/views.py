from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse
from django.http import Http404

from pydotorg.mixins import LoginRequiredMixin

from .models import Nomination, Nominee, Election
from .forms import NominationForm, NominationCreateForm


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


class NominationEdit(LoginRequiredMixin, NominationMixin, UpdateView):
    model = Nomination
    form_class = NominationForm

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
