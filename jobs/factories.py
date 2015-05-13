import datetime
import factory

from django.utils import timezone

from .models import JobType, JobCategory, Job

next_month = timezone.now() + datetime.timedelta(days=30)


class JobCategoryFactory(factory.DjangoModelFactory):

    class Meta:
        model = JobCategory
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: 'Job Category {}'.format(n))


class JobTypeFactory(factory.DjangoModelFactory):

    class Meta:
        model = JobType
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: 'Job Type {}'.format(n))


class JobFactory(factory.DjangoModelFactory):

    class Meta:
        model = Job

    category = factory.SubFactory(JobCategoryFactory)
    job_title = factory.Sequence(lambda n: 'Job Title #{}'.format(n))
    city = 'Lawrence'
    region = 'KS'
    country = 'US'
    company_name = factory.Sequence(lambda n: 'Company #{}'.format(n))
    company_description = factory.Sequence(lambda n: 'Company {} Description'.format(n))
    contact = 'John Recruiter'
    email = factory.Sequence(lambda n: 'recruiter{}@example.com'.format(n))

    description = 'Test Description'
    requirements = 'Test Requirements'

    expires = next_month

    @factory.post_generation
    def job_types(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of job_types were passed in, use them
            for job_type in extracted:
                self.job_types.add(job_type)


class ApprovedJobFactory(JobFactory):
    status = Job.STATUS_APPROVED


class ArchivedJobFactory(JobFactory):
    status = Job.STATUS_ARCHIVED


class DraftJobFactory(JobFactory):
    status = Job.STATUS_DRAFT


class ExpiredJobFactory(JobFactory):
    status = Job.STATUS_EXPIRED


class RejectedJobFactory(JobFactory):
    status = Job.STATUS_REJECTED


class RemovedJobFactory(JobFactory):
    status = Job.STATUS_REMOVED


class ReviewJobFactory(JobFactory):
    status = Job.STATUS_REVIEW
