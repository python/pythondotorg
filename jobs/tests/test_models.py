from django.test import TestCase
from django.utils import timezone

from ..factories import JobFactory
from ..models import Job


class JobsModelsTests(TestCase):
    def setUp(self):
        self.job = JobFactory(
            city='Memphis',
            region='TN',
            country='USA',
        )

    def test_is_new(self):
        self.assertTrue(self.job.is_new)

        threshold = Job.NEW_THRESHOLD

        self.job.created = timezone.now() - (threshold * 2)
        self.assertFalse(self.job.is_new)

    def test_location_slug(self):
        self.assertEqual(self.job.location_slug, 'memphis-tn-usa')
