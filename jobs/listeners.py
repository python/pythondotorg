from django.db import models
from django.contrib.sites.models import Site
from django.template import loader, Context
from django.utils.translation import ugettext_lazy as _
from django_comments_xtd.conf import settings
from django_comments_xtd.utils import send_mail


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


def on_job_was_approved(sender, job, approving_user, **kwargs):
    """Handle approving job offer. Currently an email should be sent to the
    person that sent the offer.
    """
    subject_template = loader.get_template(
            'jobs/email/job_was_approved_subject.txt')
    message_template = loader.get_template('jobs/email/job_was_approved.txt')
    reviewer_name = '{0} {1}'.format(approving_user.first_name,
                                     approving_user.last_name)
    message_context = Context({'addressee': job.contact,
                               'reviewer_name': reviewer_name,
                              })
    # subject can't contain newlines, thus strip() call
    subject = subject_template.render(message_context).strip()
    message = message_template.render(message_context)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [job.email])
