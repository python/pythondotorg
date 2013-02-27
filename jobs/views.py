from django.views.generic import ListView, DetailView, CreateView
from django.utils import timezone

import datetime

from .forms import JobForm
from .models import Job


class JobList(ListView):
    model = Job

    def get_queryset(self):
        threshold = timezone.now() - datetime.timedelta(days=90)

        return Job.objects.select_related().filter(created__gt=threshold)


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


class JobDetail(DetailView):
    model = Job

    def get_queryset(self):
        threshold = timezone.now() - datetime.timedelta(days=90)

        return Job.objects.select_related().filter(created__gt=threshold)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category_jobs'] = self.object.category.jobs.select_related('company__name')[:5]
        return ctx


class JobCreate(CreateView):
    model = Job
    form_class = JobForm

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
