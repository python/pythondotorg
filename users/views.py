from django.contrib.auth import authenticate, login
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView, DetailView, ListView, TemplateView, UpdateView
)

from allauth.account.views import SignupView
from honeypot.decorators import check_honeypot

from pydotorg.mixins import LoginRequiredMixin

from .forms import (
    UserProfileForm, MembershipForm, MembershipUpdateForm,
)
from .models import User, Membership
from .paginators import UserPaginator


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


class UserList(ListView):
    paginate_by = 25
    paginator_class = UserPaginator

    def get_queryset(self):
        return User.objects.searchable()


class HoneypotSignupView(SignupView):

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
