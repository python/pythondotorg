from django.test import TestCase

from ..models import Job, JobCategory

from django.utils import timezone


class JobsModelsTests(TestCase):
    def setUp(self):
        job_category = JobCategory.objects.create(
            name='Game Production',
            slug='game-production'
        )

        self.job = Job.objects.create(
            company='Kulfun Games',
            description='Lorem ipsum dolor sit amet',
            category=job_category,
            city='Memphis',
            region='TN',
            country='USA'
        )

    def test_is_new(self):
        self.assertTrue(self.job.is_new)

        threshold = Job.NEW_THRESHOLD

        self.job.created = timezone.now() - (threshold * 2)
        self.assertFalse(self.job.is_new)

    def test_location_slug(self):
        self.assertEqual(self.job.location_slug, 'memphis-tn-usa')
