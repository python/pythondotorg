import datetime

from braces.views import LoginRequiredMixin, SuperuserRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View

from .forms import JobForm
from .models import Job


class JobList(ListView):
    model = Job
    paginate_by = 25

    def get_queryset(self):
        threshold = timezone.now() - datetime.timedelta(days=30)
        return super().get_queryset().approved().select_related().filter(created__gt=threshold)


class JobListMine(ListView):
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


class JobReview(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
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


class JobDetail(DetailView):
    model = Job

    def get_queryset(self):
        threshold = timezone.now() - datetime.timedelta(days=90)

        return Job.objects.select_related().filter(created__gt=threshold)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            category_jobs=self.object.category.jobs.select_related('company__name')[:5],
            user_can_edit=(self.object.creator == self.request.user),
            **kwargs
        )


class JobDetailReview(LoginRequiredMixin, SuperuserRequiredMixin, JobDetail):

    def get_queryset(self):
        # TODO: Add moderator info...
        return Job.objects.all()

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            user_can_edit=(self.object.creator == self.request.user),
            under_review=True,
            **kwargs
        )


class JobCreate(CreateView):
    model = Job
    form_class = JobForm

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class JobEdit(UpdateView):
    model = Job
    form_class = JobForm

    def get_queryset(self):
        return self.request.user.job_set.all()
        #return self.request.user.job_set.exclude(status=self.model.STATUS_APPROVED)


class JobChangeStatus(LoginRequiredMixin, View):
    """
    Abstract class to change a job's status; see the concrete implentations below.
    """
    def post(self, request, pk):
        job = get_object_or_404(self.request.user.job_set, pk=pk)
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
