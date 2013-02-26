from django.views.generic import ListView, DetailView
from django.utils import timezone

import datetime

from .models import Job


class JobList(ListView):
    model = Job

    def get_queryset(self):
        threshold = timezone.now() - datetime.timedelta(days=90)

        return Job.objects.select_related().filter(created__gt=threshold)


class JobListType(JobList):
    def get_queryset(self):
        return super().get_queryset().filter(job_types__slug=self.kwargs['slug'])


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
