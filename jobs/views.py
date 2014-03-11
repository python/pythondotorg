import datetime

from braces.views import LoginRequiredMixin, SuperuserRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View

from .forms import JobForm
from .models import Job, JobType, JobCategory
from companies.models import Company

THRESHOLD_DAYS = 90


class JobMixin(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jobs_count'] = Job.objects.approved().count()
        context['companies_count'] = Company.objects.filter(jobs__status=Job.STATUS_APPROVED, jobs__isnull=False).distinct().count()
        context['featured_companies'] = Company.objects.filter(jobs__is_featured=True, jobs__status=Job.STATUS_APPROVED).distinct()
        return context

class JobList(JobMixin, ListView):
    model = Job
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().approved().select_related()


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


class JobListType(JobList):
    def get_queryset(self):
        return super().get_queryset().filter(job_types__slug=self.kwargs['slug'])


class JobListCompany(JobList):
    def get_queryset(self):
        return super().get_queryset().filter(company__slug=self.kwargs['slug'])


class JobListCategory(JobList):
    def get_queryset(self):
        return super().get_queryset().filter(category__slug=self.kwargs['slug'])


class JobListLocation(JobList):
    def get_queryset(self):
        return super().get_queryset().filter(location_slug=self.kwargs['slug'])


class JobTypes(JobMixin, TemplateView):
    """ View to simply list JobType instances that have current jobs """
    template_name = "jobs/job_types.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        threshold = timezone.now() - datetime.timedelta(days=THRESHOLD_DAYS)
        context['types'] = JobType.objects.filter(
            jobs__status=Job.STATUS_APPROVED,
            jobs__created__gt=threshold,
        ).distinct().order_by('name')

        return context


class JobCategories(JobMixin, TemplateView):
    """ View to simply list JobCategory instances that have current jobs """
    template_name = "jobs/job_categories.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        threshold = timezone.now() - datetime.timedelta(days=THRESHOLD_DAYS)
        context['categories'] = JobCategory.objects.filter(
            jobs__status=Job.STATUS_APPROVED,
            jobs__created__gt=threshold,
        ).distinct().order_by('name')

        return context


class JobLocations(JobMixin, TemplateView):
    """ View to simply list distinct Countries that have current jobs """
    template_name = "jobs/job_locations.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        threshold = timezone.now() - datetime.timedelta(days=THRESHOLD_DAYS)
        context['jobs'] = Job.objects.approved().filter(
            created__gt=threshold
        ).order_by('country', 'region')

        return context


class JobReview(LoginRequiredMixin, SuperuserRequiredMixin, JobMixin, ListView):
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
            job.status = Job.STATUS_APPROVED
            job.save()
            messages.add_message(self.request, messages.SUCCESS, "'%s' approved." % job)

        elif action == 'reject':
            job.status = Job.STATUS_REJECTED
            job.save()
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
        threshold = timezone.now() - datetime.timedelta(days=90)

        return Job.objects.select_related().filter(created__gt=threshold)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(
            category_jobs=self.object.category.jobs.select_related('company__name')[:5],
            user_can_edit=(self.object.creator == self.request.user)
        )
        ctx.update(kwargs)
        return ctx


class JobDetailReview(LoginRequiredMixin, SuperuserRequiredMixin, JobDetail):

    def get_queryset(self):
        # TODO: Add moderator info...
        return Job.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(
            user_can_edit=(self.object.creator == self.request.user),
            under_review=True,
        )
        ctx.update(kwargs)
        return ctx


class JobCreate(JobMixin, CreateView):
    model = Job
    form_class = JobForm

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class JobEdit(JobMixin, UpdateView):
    model = Job
    form_class = JobForm

    def get_queryset(self):
        return self.request.user.jobs_job_creator.all()
        #return self.request.user.jobs_job_creator.exclude(status=self.model.STATUS_APPROVED)


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
