import datetime
from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def job_location_url(job):
    if job.location:
        return reverse('jobs:job_filter_location', kwargs={
            'city_slug': job.location.slug,
            'region_slug': job.location.region.slug,
            'country_slug': job.location.country.slug,
        })
    return reverse('jobs:job_list_location', kwargs={'slug': job.location_slug})
