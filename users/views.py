from braces.views import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from honeypot.decorators import check_honeypot

from .forms import UserCreationForm, UserProfileForm, MembershipForm
from .models import User, Membership


#TODO: dont show the form if the user is already auth'd.
class SignupView(CreateView):
    form_class = UserCreationForm
    model = User

    def get_success_url(self):
        return '/'

    @method_decorator(check_honeypot)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return render(request, 'users/already_a_user.html')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super().form_valid(form)


class MembershipUpdate(CreateView):
    form_class = MembershipForm
    model = Membership
    template_name = 'users/membership_form.html'

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if self.request.user.is_authenticated():
            self.object.creator = self.request.user
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('users:user_membership_thanks')


class MembershipThanks(TemplateView):
    template_name = 'users/membership_thanks.html'


class UserUpdate(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm
    model = User
    slug_field = 'username'
    template_name = 'users/user_form.html'

    @method_decorator(check_honeypot)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return User.objects.get(username=self.request.user)


class UserDetail(DetailView):
    model = User
    slug_field = 'username'

    def get_queryset(self):
        return super().get_queryset().searchable()


class UserList(ListView):
    model = User
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().searchable()
