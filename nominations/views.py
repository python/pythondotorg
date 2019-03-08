from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse
from django.http import Http404

from pydotorg.mixins import LoginRequiredMixin

from .models import Nomination, Nominee, Election
from .forms import NominationForm, NominationCreateForm


class ElectionsList(ListView):
    model = Election


class NominationMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.election = Election.objects.get(slug=self.kwargs["election"])
        context["election"] = self.election
        return context


class NominationCreate(LoginRequiredMixin, NominationMixin, CreateView):
    model = Nomination
    form_class = NominationCreateForm

    login_message = "Please login to make a nomination."

    def get_success_url(self):
        return reverse(
            "nominations:nomination_detail",
            kwargs={"election": self.object.election.slug, "pk": self.object.id},
        )

    def form_valid(self, form):
        form.instance.nominator = self.request.user
        form.instance.election = Election.objects.get(slug=self.kwargs["election"])
        if form.cleaned_data.get('self_nomination', False):
            try:
                nominee = Nominee.objects.get(user=self.request.user, election=form.instance.election)
            except Nominee.DoesNotExist:
                nominee = Nominee.objects.create(
                    user=self.request.user,
                    election=form.instance.election,
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    previous_board_service=form.cleaned_data['previous_board_service'],
                    employer=form.cleaned_data['employer'],
                    other_affiliations=form.cleaned_data['other_affiliations'],
                )
            form.instance.nominee = nominee
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class NominationEdit(LoginRequiredMixin, NominationMixin, UpdateView):
    model = Nomination
    form_class = NominationForm

    #    def get_queryset(self):
    #        if self.has_jobs_board_admin_access():
    #            return Nomination.objects.select_related()
    #        return self.request.user.jobs_job_creator.editable()

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
        context["editable"] = self.object.editable(user=request.user)
        return self.render_to_response(context)

    def get_queryset(self):
        queryset = Nomination.objects.select_related()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
