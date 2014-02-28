from django.test import TestCase

from ..forms import FeedbackForm, FeedbackMiniForm


class FeedbackFormTests(TestCase):

    urls = 'feedbacks.urls'

    def test_feedback_form_valid(self):
        post_dict = {'comment': 'Thanks for all the fish!'}
        form = FeedbackForm(data=post_dict)
        self.assertTrue(form.is_valid())

    def test_feedback_form_error(self):
        post_dict = {'comment': ''}
        form = FeedbackForm(data=post_dict)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['comment'], ['This field is required.'])

    def test_feedback_mini_form_valid(self):
        post_dict = {'comment': 'Thanks for all the fish!'}
        form = FeedbackMiniForm(data=post_dict)
        self.assertTrue(form.is_valid())

    def test_feedback_mini_form_error(self):
        post_dict = {'comment': ''}
        form = FeedbackMiniForm(data=post_dict)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['comment'], ['This field is required.'])
