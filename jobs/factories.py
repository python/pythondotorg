"""Factory classes for creating test data in the jobs app."""

import datetime

import factory
from django.contrib.auth.models import Group
from django.utils import timezone
from factory.django import DjangoModelFactory
from faker.providers import BaseProvider

from jobs.models import Job, JobCategory, JobType
from users.factories import UserFactory


class JobProvider(BaseProvider):
    """Faker provider supplying realistic job board test data."""

    job_types = [
        "Big Data",
        "Cloud",
        "Database",
        "Evangelism",
        "Systems",
        "Test",
        "Web",
        "Operations",
    ]

    job_categories = [
        "Software Developer",
        "Software Engineer",
        "Data Analyst",
        "Administrator",
    ]

    job_titles = [
        "Senior Python Developer",
        "Django Developer",
        "Full Stack Python/Django Developer",
        "Machine Learning Engineer",
        "Full Stack Developer",
        "Python Data Engineer",
        "Senior Test Automation Engineer",
        "Backend Python Engineer",
        "Python Tech Lead",
        "Junior Developer",
    ]

    def job_type(self):
        """Return a random job type string."""
        return self.random_element(self.job_types)

    def job_category(self):
        """Return a random job category string."""
        return self.random_element(self.job_categories)

    def job_title(self):
        """Return a random job title string."""
        return self.random_element(self.job_titles)


factory.Faker.add_provider(JobProvider)


class JobCategoryFactory(DjangoModelFactory):
    """Factory for creating JobCategory instances."""

    class Meta:
        """Meta configuration for JobCategoryFactory."""

        model = JobCategory
        django_get_or_create = ("name",)

    name = factory.Faker("job_category")


class JobTypeFactory(DjangoModelFactory):
    """Factory for creating JobType instances."""

    class Meta:
        """Meta configuration for JobTypeFactory."""

        model = JobType
        django_get_or_create = ("name",)

    name = factory.Faker("job_type")


class JobFactory(DjangoModelFactory):
    """Factory for creating Job instances with default test data."""

    class Meta:
        """Meta configuration for JobFactory."""

        model = Job

    creator = factory.SubFactory(UserFactory)
    category = factory.SubFactory(JobCategoryFactory)
    job_title = factory.Faker("job_title")
    city = "Lawrence"
    region = "KS"
    country = "US"
    company_name = factory.Faker("company")
    company_description = factory.Faker("sentence", nb_words=10)
    contact = factory.Faker("name")
    email = factory.Faker("email")
    url = "https://www.example.com/"

    description = "Test Description"
    requirements = "Test Requirements"

    @factory.lazy_attribute
    def expires(self):
        """Set expiration to 30 days from now."""
        return timezone.now() + datetime.timedelta(days=30)

    @factory.post_generation
    def job_types(self, create, extracted, **kwargs):
        """Add job types to the job after creation."""
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of job_types were passed in, use them
            for job_type in extracted:
                self.job_types.add(job_type)


class ApprovedJobFactory(JobFactory):
    """Factory for creating approved job listings."""

    status = Job.STATUS_APPROVED


class ArchivedJobFactory(JobFactory):
    """Factory for creating archived job listings."""

    status = Job.STATUS_ARCHIVED


class DraftJobFactory(JobFactory):
    """Factory for creating draft job listings."""

    status = Job.STATUS_DRAFT


class ExpiredJobFactory(JobFactory):
    """Factory for creating expired job listings."""

    status = Job.STATUS_EXPIRED


class RejectedJobFactory(JobFactory):
    """Factory for creating rejected job listings."""

    status = Job.STATUS_REJECTED


class RemovedJobFactory(JobFactory):
    """Factory for creating removed job listings."""

    status = Job.STATUS_REMOVED


class ReviewJobFactory(JobFactory):
    """Factory for creating job listings in review status."""

    status = Job.STATUS_REVIEW


class JobsBoardAdminGroupFactory(DjangoModelFactory):
    """Factory for creating the Job Board Admin group."""

    class Meta:
        """Meta configuration for JobsBoardAdminGroupFactory."""

        model = Group
        django_get_or_create = ("name",)

    name = "Job Board Admin"


def initial_data():
    """Create seed job listings and admin group for development."""
    return {
        "jobs": [
            ArchivedJobFactory(),
            DraftJobFactory(),
            ExpiredJobFactory(),
            RejectedJobFactory(),
            RemovedJobFactory(),
            *ApprovedJobFactory.create_batch(size=5),
            *ReviewJobFactory.create_batch(size=3),
        ],
        "groups": [
            JobsBoardAdminGroupFactory(),
        ],
    }
