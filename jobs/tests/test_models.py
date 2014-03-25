from django.test import TestCase
from django.utils import timezone

from .. import factories
from ..models import Job


class JobsModelsTests(TestCase):
    def setUp(self):
        self.job = factories.JobFactory(
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

    def test_approved_manager(self):
        self.assertEqual(Job.objects.approved().count(), 0)
        factories.ApprovedJobFactory()
        self.assertEqual(Job.objects.approved().count(), 1)

    def test_archived_manager(self):
        self.assertEqual(Job.objects.archived().count(), 0)
        factories.ArchivedJobFactory()
        self.assertEqual(Job.objects.archived().count(), 1)

    def test_draft_manager(self):
        self.assertEqual(Job.objects.draft().count(), 0)
        factories.DraftJobFactory()
        self.assertEqual(Job.objects.draft().count(), 1)

    def test_expired_manager(self):
        self.assertEqual(Job.objects.expired().count(), 0)
        factories.ExpiredJobFactory()
        self.assertEqual(Job.objects.expired().count(), 1)

    def test_rejected_manager(self):
        self.assertEqual(Job.objects.rejected().count(), 0)
        factories.RejectedJobFactory()
        self.assertEqual(Job.objects.rejected().count(), 1)

    def test_removed_manager(self):
        self.assertEqual(Job.objects.removed().count(), 0)
        factories.RemovedJobFactory()
        self.assertEqual(Job.objects.removed().count(), 1)

    def test_review_manager(self):
        self.assertEqual(Job.objects.review().count(), 1)
        factories.ReviewJobFactory()
        self.assertEqual(Job.objects.review().count(), 2)
