from braces.views import LoginRequiredMixin, GroupRequiredMixin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View

from .forms import JobForm
from .models import Job, JobType, JobCategory


class JobBoardAdminRequiredMixin(GroupRequiredMixin):
    group_required = "Job Board Admin"


class JobMixin(object):
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
        })

        return context


class JobList(JobMixin, ListView):
    model = Job
    paginate_by = 25

    job_list_view = True

    def get_queryset(self):
        return super().get_queryset().visible().select_related()


class JobListMine(JobMixin, ListView):
    model = Job
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated():
            q = Q(creator=self.request.user)
        else:
            raise Http404
        return queryset.filter(q)


class JobTypeMenu(object):
    def job_type_view(self):
        return True


class JobCategoryMenu(object):
    def job_category_view(self):
        return True


class JobLocationMenu(object):
    def job_location_view(self):
        return True


class JobListType(JobTypeMenu, JobList):
    template_name = 'jobs/job_type_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(job_types__slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_type'] = JobType.objects.get(slug=self.kwargs['slug'])
        return context


class JobListCategory(JobCategoryMenu, JobList):
    template_name = 'jobs/job_category_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(category__slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_category'] = JobCategory.objects.get(slug=self.kwargs['slug'])
        return context


class JobListLocation(JobLocationMenu, JobList):
    template_name = 'jobs/job_location_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(location_slug=self.kwargs['slug'])


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

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['jobs'] = Job.objects.visible().distinct(
            'country', 'city'
        ).order_by(
            'country', 'city'
        )

        return context


class JobReview(LoginRequiredMixin, JobBoardAdminRequiredMixin, JobMixin, ListView):
    template_name = 'jobs/job_review.html'
    paginate_by = 20

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
            messages.add_message(self.request, messages.SUCCESS, "'%s' removed." % job)

        return redirect('jobs:job_review')


class JobDetail(JobMixin, DetailView):
    model = Job

    def get_queryset(self):
        """ Show only approved jobs to the public, staff can see all jobs """
        qs = Job.objects.select_related()

        if self.request.user.is_staff:
            return qs
        else:
            return qs.visible()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(
            category_jobs=self.object.category.jobs.select_related('company__name')[:5],
            user_can_edit=(self.object.creator == self.request.user)
        )
        ctx.update(kwargs)
        return ctx


class JobDetailReview(LoginRequiredMixin, JobBoardAdminRequiredMixin, JobDetail):

    def get_queryset(self):
        """ Only staff and creator can review """
        if self.request.user.is_staff:
            return Job.objects.select_related()
        else:
            raise Http404()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(
            user_can_edit=(
                self.object.creator == self.request.user
                or self.request.user.is_staff
            ),
            under_review=True,
        )
        ctx.update(kwargs)
        return ctx


class JobCreateEditMixin(object):

    def form_valid(self, form):
        self.object = form.save()
        
        # Clear existing job types
        self.object.job_types.clear()

        # Add all of the chosen ones
        for t in form.cleaned_data['job_types']:
            self.object.job_types.add(t)

        return super().form_valid(form)


class JobCreate(JobMixin, JobCreateEditMixin, CreateView):
    model = Job
    form_class = JobForm

    def get_success_url(self):
        return reverse('jobs:job_thanks')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        if self.request.user.is_authenticated():
            kwargs['initial'] = {'email': self.request.user.email}
        return kwargs

    def form_valid(self, form):
        """ set the creator to the current user """
        form = super().form_valid(form)

        # Associate Job to user if they are logged in
        if self.request.user.is_authenticated():
            self.object.creator = self.request.user
            self.object.save()

        return form


class JobEdit(JobMixin, JobCreateEditMixin, UpdateView):
    model = Job
    form_class = JobForm

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return self.request.user.jobs_job_creator.all()

    def form_valid(self, form):
        """ set last_modified_by to the current user """
        form = super().form_valid(form)
        self.object.last_modified_by = self.request.user
        self.object.save()

        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(
            form_action='update',
        )
        ctx.update(kwargs)
        return ctx


class JobChangeStatus(LoginRequiredMixin, JobMixin, View):
    """
    Abstract class to change a job's status; see the concrete implentations below.
    """
    def post(self, request, pk):
        job = get_object_or_404(self.request.user.jobs_job_creator, pk=pk)
        job.status = self.new_status
        job.save()
        messages.add_message(self.request, messages.SUCCESS, self.success_message)
        return redirect('job_detail', job.id)


class JobPublish(JobChangeStatus):
    new_status = Job.STATUS_APPROVED
    success_message = 'Your job listing has been published.'


class JobArchive(JobChangeStatus):
    new_status = Job.STATUS_ARCHIVED
    success_message = 'Your job listing has been archived and is no longer public.'
