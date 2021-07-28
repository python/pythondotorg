from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.template import loader
from django.utils.translation import ugettext_lazy as _

from .models import Job
from .signals import (
    job_was_submitted, job_was_approved, job_was_rejected, comment_was_posted,
)

# Python job board team email address
EMAIL_JOBS_BOARD = 'jobs@python.org'


@receiver(comment_was_posted)
def on_comment_was_posted(sender, comment, **kwargs):
    """
    Notify the author of the post when the first comment has been posted.
    """
    if not comment.comment:
        return False
    job = comment.job
    if job.creator is None:
        name = job.contact or 'Job Submitter'
    else:
        name = (
            job.creator.get_full_name() or job.creator.get_username() or
            job.contact or 'Job Submitter'
        )
    send_to = [EMAIL_JOBS_BOARD]
    reviewer_name = (
        comment.creator.get_full_name() or comment.creator.get_username() or
        'Community Reviewer'
    )
    is_job_board_admin = job.creator.email != comment.creator.email
    context = {
        'comment': comment.comment.raw,
        'content_object': job,
        'site': Site.objects.get_current(),
    }

    if is_job_board_admin:
        # Send email to both jobs@p.o and creator's email when
        # job board admins left a comment.
        send_to.append(job.email)

        context['user_name'] = name
        context['reviewer_name'] = reviewer_name
        template_name = 'comment_was_posted'
    else:
        context['submitter_name'] = name
        template_name = 'comment_was_posted_admin'

    subject = _("Python Job Board: Review comment for: {}").format(
        job.display_name)
    text_message_template = loader.get_template(f'jobs/email/{template_name}.txt')

    text_message = text_message_template.render(context)
    send_mail(subject, text_message, settings.JOB_FROM_EMAIL, send_to)


def send_job_review_message(job, user, subject_template_path,
                            message_template_path):
    """Helper function wrapping logic of sending the review message concerning
    a job.

    `user` param holds user that performed the review action.
    """
    subject_template = loader.get_template(subject_template_path)
    message_template = loader.get_template(message_template_path)
    reviewer_name = user.get_full_name() or user.username or 'Community Reviewer'
    context = {
        'user_name': job.contact or 'Job Submitter',
        'reviewer_name': reviewer_name,
        'content_object': job,
        'site': Site.objects.get_current(),
    }
    # subject can't contain newlines, thus strip() call
    subject = subject_template.render(context).strip()
    message = message_template.render(context)
    send_mail(subject, message, settings.JOB_FROM_EMAIL,
              [job.email, EMAIL_JOBS_BOARD])


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


@receiver(job_was_submitted)
def on_job_was_submitted(sender, job, **kwargs):
    """
    Notify the jobs board when a new job has been submitted for approval

    """
    subject_template = loader.get_template('jobs/email/job_was_submitted_subject.txt')
    message_template = loader.get_template('jobs/email/job_was_submitted.txt')

    context = {'content_object': job, 'site': Site.objects.get_current()}
    subject = subject_template.render(context)
    message = message_template.render(context)

    send_mail(subject, message, settings.JOB_FROM_EMAIL,
              [EMAIL_JOBS_BOARD])
