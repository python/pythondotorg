"""Haystack search indexes for the jobs app."""

from django.template.defaultfilters import striptags, truncatewords_html
from django.urls import reverse
from haystack import indexes

from .models import Job, JobCategory, JobType


class JobTypeIndex(indexes.SearchIndex, indexes.Indexable):
    """Search index for job types with active jobs."""

    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")
    path = indexes.CharField()

    include_template = indexes.CharField()

    def get_model(self):
        """Return the JobType model class."""
        return JobType

    def index_queryset(self, using=None):
        """Return job types that have active jobs."""
        return JobType.objects.with_active_jobs()

    def prepare_include_template(self, obj):
        """Return the search result template path."""
        return "search/includes/jobs.job_type.html"

    def prepare_path(self, obj):
        """Return the URL for jobs of this type."""
        return reverse("jobs:job_list_type", kwargs={"slug": obj.slug})

    def prepare(self, obj):
        """Boost job type results in search."""
        data = super().prepare(obj)
        data["boost"] = 1.3
        return data


class JobCategoryIndex(indexes.SearchIndex, indexes.Indexable):
    """Search index for job categories with active jobs."""

    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")
    path = indexes.CharField()

    include_template = indexes.CharField()

    def get_model(self):
        """Return the JobCategory model class."""
        return JobCategory

    def index_queryset(self, using=None):
        """Return job categories that have active jobs."""
        return JobCategory.objects.with_active_jobs()

    def prepare_include_template(self, obj):
        """Return the search result template path."""
        return "search/includes/jobs.job_category.html"

    def prepare_path(self, obj):
        """Return the URL for jobs in this category."""
        return reverse("jobs:job_list_category", kwargs={"slug": obj.slug})

    def prepare(self, obj):
        """Boost job category results in search."""
        data = super().prepare(obj)
        data["boost"] = 1.4
        return data


class JobIndex(indexes.SearchIndex, indexes.Indexable):
    """Search index for visible job listings."""

    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="job_title")
    city = indexes.CharField(model_attr="city")
    region = indexes.CharField(model_attr="region")
    country = indexes.CharField(model_attr="country")
    telecommuting = indexes.BooleanField(model_attr="telecommuting")

    description = indexes.CharField()

    path = indexes.CharField()

    include_template = indexes.CharField()

    def get_model(self):
        """Return the Job model class."""
        return Job

    def index_queryset(self, using=None):
        """Return publicly visible jobs."""
        return Job.objects.visible()

    def prepare_include_template(self, obj):
        """Return the search result template path."""
        return "search/includes/jobs.job.html"

    def prepare_description(self, obj):
        """Return a truncated plain-text job description."""
        return striptags(truncatewords_html(obj.description.rendered, 50))

    def prepare_path(self, obj):
        """Return the URL for this job listing."""
        return reverse("jobs:job_detail", kwargs={"pk": obj.pk})

    def prepare(self, obj):
        """Boost job listing results in search."""
        data = super().prepare(obj)
        data["boost"] = 1.1
        return data
