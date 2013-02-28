from django.test import TestCase
from django.utils import timezone

from companies.models import Company

from ..models import Job, JobCategory


class JobsModelsTests(TestCase):
    def setUp(self):
        company = Company.objects.create(
            name='Kulfun Games',
            slug='kulfun-games',
        )

        job_category = JobCategory.objects.create(
            name='Game Production',
            slug='game-production'
        )

        self.job = Job.objects.create(
            company=company,
            description='Lorem ipsum dolor sit amet',
            category=job_category,
            city='Memphis',
            region='TN',
            country='USA',
            email='hr@company.com'
        )

    def test_is_new(self):
        self.assertTrue(self.job.is_new)

        threshold = Job.NEW_THRESHOLD

        self.job.created = timezone.now() - (threshold * 2)
        self.assertFalse(self.job.is_new)

    def test_location_slug(self):
        self.assertEqual(self.job.location_slug, 'memphis-tn-usa')
