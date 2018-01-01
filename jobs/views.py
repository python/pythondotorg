from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View

from pydotorg.mixins import GroupRequiredMixin, LoginRequiredMixin

from .forms import JobForm, JobReviewCommentForm
from .models import Job, JobType, JobCategory, JobReviewComment


class JobListMenu:
    def job_list_view(self):
        return True


class JobTypeMenu:
    def job_type_view(self):
        return True


class JobCategoryMenu:
    def job_category_view(self):
        return True


class JobLocationMenu:
    def job_location_view(self):
        return True


class JobBoardAdminRequiredMixin(GroupRequiredMixin):
    group_required = "Job Board Admin"
    raise_exception = True

    def check_membership(self, group):
        # Add is_staff check to stay compatible with current staff members.
        # is_superuser check is already in base class.
        if self.request.user.is_staff:
            return True
        return super().check_membership(group)


class JobMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_locations = Job.objects.visible().distinct(
            'location_slug'
        ).order_by(
            'location_slug',
        )

        context.update({
            'jobs_count': Job.objects.visible().count(),
            'active_types': JobType.objects.with_active_jobs(),
            'active_categories': JobCategory.objects.with_active_jobs(),
            'active_locations': active_locations,
            'jobs_board_admin': self.has_jobs_board_admin_access(),
        })

        return context

    def has_jobs_board_admin_access(self):
        # Add is_staff and is_superuser checks to stay compatible
        # with current staff members.
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        user_groups = self.request.user.groups.values_list('name', flat=True)
        return JobBoardAdminRequiredMixin.group_required in user_groups


class JobList(JobListMenu, JobMixin, ListView):
    model = Job
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().visible().select_related()


class JobListMine(LoginRequiredMixin, JobMixin, ListView):
    paginate_by = 25

    def get_queryset(self):
        return Job.objects.by(self.request.user).select_related()


class JobListType(JobTypeMenu, JobMixin, ListView):
    paginate_by = 25
    template_name = 'jobs/job_type_list.html'

    def get_queryset(self):
        self.current_type = get_object_or_404(JobType,
                                              slug=self.kwargs['slug'])
        return Job.objects.visible().select_related().filter(
            job_types__slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_type'] = self.current_type
        return context


class JobListCategory(JobCategoryMenu, JobMixin, ListView):
    paginate_by = 25
    template_name = 'jobs/job_category_list.html'

    def get_queryset(self):
        self.current_category = get_object_or_404(JobCategory,
                                                  slug=self.kwargs['slug'])
        return Job.objects.visible().select_related().filter(
            category__slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_category'] = self.current_category
        return context


class JobListLocation(JobLocationMenu, JobMixin, ListView):
    paginate_by = 25
    template_name = 'jobs/job_location_list.html'

    def get_queryset(self):
        return Job.objects.visible().select_related().filter(
            location_slug=self.kwargs['slug'])


class JobTypes(JobTypeMenu, JobMixin, ListView):
    """ View to simply list JobType instances that have current jobs """
    template_name = "jobs/job_types.html"
    queryset = JobType.objects.with_active_jobs().order_by('name')
    context_object_name = 'types'


class JobCategories(JobCategoryMenu, JobMixin, ListView):
    """ View to simply list JobCategory instances that have current jobs """
    template_name = "jobs/job_categories.html"
    queryset = JobCategory.objects.with_active_jobs().order_by('name')
    context_object_name = 'categories'


class JobLocations(JobLocationMenu, JobMixin, TemplateView):
    """ View to simply list distinct Countries that have current jobs """
    template_name = "jobs/job_locations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['jobs'] = Job.objects.visible().distinct(
            'country', 'city'
        ).order_by(
            'country', 'city'
        )

        return context


class JobTelecommute(JobLocationMenu, JobList):
    """ Specific view for telecommute jobs """
    template_name = 'jobs/job_telecommute_list.html'

    def get_queryset(self):
        return super().get_queryset().visible().select_related().filter(
            telecommuting=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jobs_count'] = len(self.object_list)
        context['jobs'] = self.object_list
        return context


class JobReview(LoginRequiredMixin, JobBoardAdminRequiredMixin, JobMixin, ListView):
    template_name = 'jobs/job_review.html'
    paginate_by = 20
    redirect_url = 'jobs:job_review'

    def get_queryset(self):
        return Job.objects.review()

    def post(self, request):
        try:
            job = Job.objects.get(id=request.POST['job_id'])
            action = request.POST['action']
        except (KeyError, Job.DoesNotExist):
            return redirect('jobs:job_review')

        if action == 'approve':
            job.approve(request.user)
            messages.add_message(self.request, messages.SUCCESS, "'%s' approved." % job)

        elif action == 'reject':
            job.reject(request.user)
            messages.add_message(self.request, messages.SUCCESS, "'%s' rejected." % job)

        elif action == 'remove':
            job.status = Job.STATUS_REMOVED
            job.save()
            messages.add_message(self.request, messages.SUCCESS, "'%s' removed." % job)

        elif action == 'archive':
            job.status = Job.STATUS_ARCHIVED
            job.save()
            messages.add_message(self.request, messages.SUCCESS, "'%s' archived." % job)
        else:
            raise Http404

        return redirect(self.redirect_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'review'
        return context


class JobModerateList(JobReview):
    redirect_url = 'jobs:job_moderate'

    def get_queryset(self):
        queryset = Job.objects.moderate()
        q = self.request.GET.get('q')
        if q is not None:
            return queryset.filter(job_title__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'moderate'
        return context


class JobDetail(JobMixin, DetailView):

    def get_queryset(self):
        queryset = Job.objects.select_related()
        if self.has_jobs_board_admin_access():
            return queryset
        if self.request.user.is_authenticated:
            # Combine visible jobs and user's non-visible jobs.
            # TODO: Add this to JobQuerySet and use where applicable.
            return queryset.visible() | queryset.by(self.request.user)
        return queryset.visible()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_jobs'] = self.object.category.jobs.select_related('category')[:5]
        context['user_can_edit'] = (
            self.object.creator == self.request.user or
            self.has_jobs_board_admin_access()
        ) and self.object.editable
        context['job_review_form'] = JobReviewCommentForm(initial={'job': self.object})
        return context


class JobPreview(LoginRequiredMixin, JobDetail, UpdateView):
    template_name = 'jobs/job_detail.html'
    form_class = JobForm

    def get_success_url(self):
        return reverse('jobs:job_thanks')

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        self.object = self.get_object()
        if self.request.POST.get('action') == 'review':
            self.object.review()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request)

    def get_object(self, queryset=None):
        """ Show only approved jobs to the public, staff can see all jobs """
        job = super().get_object(queryset=queryset)
        # Only allow creator to preview and only while in draft status
        if job.creator == self.request.user and job.editable:
            return job

        if self.request.user.is_staff:
            return job

        if not job.editable:
            raise Http404
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_can_edit'] = (
            self.object.creator == self.request.user or
            self.has_jobs_board_admin_access()
        ) and self.object.editable
        context['under_preview'] = True
        # TODO: why we pass this?
        context['form'] = self.get_form(self.form_class)
        return context


class JobReviewCommentCreate(LoginRequiredMixin, JobMixin, CreateView):
    model = JobReviewComment
    form_class = JobReviewCommentForm

    def get_success_url(self):
        return reverse('jobs:job_detail', kwargs={'pk': self.request.POST.get('job')})

    def form_valid(self, form):
        if (self.request.user.username != form.instance.job.creator.username and not
                self.has_jobs_board_admin_access()):
            return HttpResponse('Unauthorized', status=401)
        action = self.request.POST.get('action')
        valid_actions = {'approve': Job.STATUS_APPROVED, 'reject': Job.STATUS_REJECTED}
        if action is not None and action in valid_actions:
            if not self.has_jobs_board_admin_access():
                return HttpResponse('Unauthorized', status=401)
            action_status = valid_actions.get(action)
            getattr(form.instance.job, action)(self.request.user)
            messages.add_message(
                self.request, messages.SUCCESS,
                "'{}' {}.".format(form.instance.job, action_status)
            )
        else:
            messages.add_message(self.request, messages.SUCCESS,
                                 'Your comment has been posted.')
        form.instance.creator = self.request.user
        return super().form_valid(form)


class JobCreate(LoginRequiredMixin, JobMixin, CreateView):
    model = Job
    form_class = JobForm

    login_message = 'Please login to create a job posting.'

    def get_success_url(self):
        return reverse('jobs:job_preview', kwargs={'pk': self.object.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        # We don't allow posting a job without logging in to the site.
        kwargs['initial'] = {'email': self.request.user.email}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['needs_preview'] = not self.has_jobs_board_admin_access()
        return context

    def form_valid(self, form):
        form.instance.creator = self.request.user
        form.instance.status = 'draft'
        return super().form_valid(form)


class JobEdit(LoginRequiredMixin, JobMixin, UpdateView):
    model = Job
    form_class = JobForm

    def get_queryset(self):
        if self.has_jobs_board_admin_access():
            return Job.objects.select_related()
        return self.request.user.jobs_job_creator.editable()

    def form_valid(self, form):
        """ set last_modified_by to the current user """
        form.instance.last_modified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_action'] = 'update'
        context['next'] = self.request.GET.get('next') or self.request.POST.get('next')
        context['needs_preview'] = not self.has_jobs_board_admin_access()
        return context

    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        elif self.object.pk:
            return reverse('jobs:job_preview', kwargs={'pk': self.object.id})
        else:
            return super().get_success_url()
