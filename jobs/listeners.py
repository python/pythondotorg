from django.db import models
from django.dispatch import receiver
from django.contrib.comments.signals import comment_was_posted
from django.contrib.sites.models import Site
from django.template import loader, Context
from django.utils.translation import ugettext_lazy as _
from django_comments_xtd.conf import settings
from django_comments_xtd.utils import send_mail

from .models import Job
from .signals import job_was_approved, job_was_rejected


@receiver(comment_was_posted)
def on_comment_was_posted(sender, comment, request, **kwargs):
    """
    Notify the author of the post when the first comment has been posted.

    Further comments subscribe automatically because our custom forms at
    `.forms.JobCommentForm` forces `follow_up` to `True` and Django-comments-xtd
    will already notify followers.
    """
    Job = models.get_model('jobs', 'Job')

    # Skip if this is not a 'first comment'
    if comment.level > 0 or comment.order > 1:
        return False

    # RSkip if we're not commenting on a Job
    model = comment.content_type.model_class()
    if model != Job:
        return False

    job = model._default_manager.get(pk=comment.object_pk)

    email = job.email
    name = job.contact


    subject = _("new comment posted")
    text_message_template = loader.get_template("django_comments_xtd/email_job_added_comment.txt")
    html_message_template = loader.get_template("django_comments_xtd/email_job_added_comment.html")

    message_context = Context({ 'user_name': name,
                                'comment': comment,
                                'content_object': job,
                                'site': Site.objects.get_current() })
    text_message = text_message_template.render(message_context)
    html_message = html_message_template.render(message_context)
    send_mail(subject, text_message, settings.DEFAULT_FROM_EMAIL, [ email, ], html=html_message)


def send_job_review_message(job, user, subject_template_path,
                            message_template_path):
    """Helper function wrapping logic of sending the review message concerning
    a job.

    `user` param holds user that performed the review action.
    """
    subject_template = loader.get_template(subject_template_path)
    message_template = loader.get_template(message_template_path)
    reviewer_name = '{} {}'.format(user.first_name, user.last_name)
    message_context = Context({'addressee': job.contact,
                               'reviewer_name': reviewer_name,
                              })
    # subject can't contain newlines, thus strip() call
    subject = subject_template.render(message_context).strip()
    message = message_template.render(message_context)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [job.email])


@receiver(job_was_approved)
def on_job_was_approved(sender, job, approving_user, **kwargs):
    """Handle approving job offer. Currently an email should be sent to the
    person that sent the offer.
    """
    send_job_review_message(job, approving_user,
                            'jobs/email/job_was_approved_subject.txt',
                            'jobs/email/job_was_approved.txt')


@receiver(job_was_rejected)
def on_job_was_rejected(sender, job, rejecting_user, **kwargs):
    """Handle rejecting job offer. Currently an email should be sent to the
    person that sent the offer.
    """
    send_job_review_message(job, rejecting_user,
                            'jobs/email/job_was_rejected_subject.txt',
                            'jobs/email/job_was_rejected.txt')


@receiver(models.signals.post_save, sender=Job, dispatch_uid="job_was_submitted")
def on_job_was_submitted(sender, instance, **kwargs):
    """
    Notify the jobs board when a new job has been submitted for approval

    """
    Job = models.get_model('jobs', 'Job')
    if instance.status != Job.STATUS_REVIEW:
        return

    subject_template = loader.get_template('jobs/email/job_was_submitted_subject.txt')
    message_template = loader.get_template('jobs/email/job_was_submitted.txt')

    message_context = Context({'content_object': instance,
                               'site': Site.objects.get_current()})
    subject = subject_template.render(message_context)
    message = message_template.render(message_context)

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, ['jobs@python.org'])
