import factory

from .models import JobType, JobCategory, Job
from companies.factories import CompanyFactory


__all__ = (
    'JobFactory',
    'JobCategoryFactory',
    'JobTypeFactory'
)


class JobCategoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = JobCategory
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = factory.Sequence(lambda n: 'Job Category {0}'.format(n))


class JobTypeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = JobType
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = factory.Sequence(lambda n: 'Job Type {0}'.format(n))


class JobFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Job

    category = factory.SubFactory(JobCategoryFactory)
    company = factory.SubFactory(CompanyFactory)
    city = 'Lawrence'
    region = 'KS'
    country = 'US'

    @factory.post_generation
    def job_types(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of job_types were passed in, use them
            for job_type in extracted:
                self.job_types.add(job_type)
