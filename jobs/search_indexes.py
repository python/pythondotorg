from django.urls import reverse
from django.template.defaultfilters import truncatewords_html, striptags

from haystack import indexes

from .models import JobType, JobCategory, Job


class JobTypeIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    path = indexes.CharField()

    include_template = indexes.CharField()

    def get_model(self):
        return JobType

    def index_queryset(self, using=None):
        return JobType.objects.with_active_jobs()

    def prepare_include_template(self, obj):
        return "search/includes/jobs.job_type.html"

    def prepare_path(self, obj):
        return reverse('jobs:job_list_type', kwargs={'slug': obj.slug})

    def prepare(self, obj):
        data = super().prepare(obj)
        data['boost'] = 1.3
        return data


class JobCategoryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    path = indexes.CharField()

    include_template = indexes.CharField()

    def get_model(self):
        return JobCategory

    def index_queryset(self, using=None):
        return JobCategory.objects.with_active_jobs()

    def prepare_include_template(self, obj):
        return "search/includes/jobs.job_category.html"

    def prepare_path(self, obj):
        return reverse('jobs:job_list_category', kwargs={'slug': obj.slug})

    def prepare(self, obj):
        data = super().prepare(obj)
        data['boost'] = 1.4
        return data


class JobIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='job_title')
    city = indexes.CharField(model_attr='city')
    region = indexes.CharField(model_attr='region')
    country = indexes.CharField(model_attr='country')
    telecommuting = indexes.BooleanField(model_attr='telecommuting')

    description = indexes.CharField()

    path = indexes.CharField()

    include_template = indexes.CharField()

    def get_model(self):
        return Job

    def index_queryset(self, using=None):
        return Job.objects.visible()

    def prepare_include_template(self, obj):
        return "search/includes/jobs.job.html"

    def prepare_description(self, obj):
        return striptags(truncatewords_html(obj.description.rendered, 50))

    def prepare_path(self, obj):
        return reverse('jobs:job_detail', kwargs={'pk': obj.pk})

    def prepare(self, obj):
        data = super().prepare(obj)
        data['boost'] = 1.1
        return data
