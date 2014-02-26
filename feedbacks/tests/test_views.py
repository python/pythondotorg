from django.core.urlresolvers import reverse
from django.test import TestCase

from ..models import Feedback, FeedbackCategory, IssueType


class FeedbackViewTests(TestCase):
    def setUp(self):
        self.name = 'Kevin Arnold'
        self.email = 'kevinarnold@example.com'

        self.issue_type_1 = IssueType.objects.create(name='Browser design bug')
        self.issue_type_2 = IssueType.objects.create(name='Feature suggestion')

        self.feature_category_1 = FeedbackCategory.objects.create(name='Python Packages')
        self.feature_category_2 = FeedbackCategory.objects.create(name='Python Community')
        self.feature_category_3 = FeedbackCategory.objects.create(name='Jobs')

    def test_feedback_create_valid(self):
        url = reverse('feedback_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        post_data = {
            'name': self.name,
            'email': self.email,
            'country': 'United States',
            'feedback_categories': [self.feature_category_2.pk, self.feature_category_3.pk],
            'issue_type': self.issue_type_2.pk,
            'comment': 'The site is great!'
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        complete_url = reverse('feedback_complete')
        self.assertRedirects(response, complete_url)

        feedbacks = Feedback.objects.filter(name__exact=self.name)
        self.assertEqual(len(feedbacks), 1)
        self.assertEqual(str(feedbacks[0]), 'Kevin Arnold')

    def test_feedback_create_invalid(self):
        url = reverse('feedback_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        post_data = {
            'name': self.name,
            'country': 'United States',
            'feedback_categories': [self.feature_category_2.pk, self.feature_category_3.pk],
            'issue_type': self.issue_type_2.pk,
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['comment'], ['This field is required.'])

    def test_feedback_beta_tester_invalid(self):
        url = reverse('feedback_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        post_data = {
            'is_beta_tester': True,
            'comment': 'Ihasbeta tester invite!'
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['email'], ['An email address is required for beta testers.'])
