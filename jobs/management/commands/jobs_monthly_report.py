import datetime

from django.core.mail import send_mail
from django.core.management import BaseCommand
from django.db.models import Count
from django.conf import settings
from django.template import loader


from jobs.models import Job


class Command(BaseCommand):
    def handle(self, **options):
        if datetime.date.today().day != 27:
            # Send only on 27th of each month
            return

        current_month = datetime.date.today().month
        current_month_jobs = (
            Job.objects.filter(created__month=current_month)
            .values("status")
            .annotate(dcount=Count("status"))
            .order_by()
        )
        current_month_jobs = {x["status"]: x["dcount"] for x in current_month_jobs}
        submissions_current_month = sum(current_month_jobs.values())

        previous_month = (
            datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        ).month
        previous_month_jobs = (
            Job.objects.filter(created__month=previous_month)
            .values("status")
            .annotate(dcount=Count("status"))
            .order_by()
        )
        previous_month_jobs = {x["status"]: x["dcount"] for x in previous_month_jobs}
        submissions_previous_month = sum(previous_month_jobs.values())

        subject_template = loader.get_template(
            "jobs/email/monthly_jobs_report_subject.txt"
        )
        message_template = loader.get_template("jobs/email/monthly_jobs_report.txt")

        context = {
            "current_month_jobs": current_month_jobs,
            "submissions_current_month": submissions_current_month,
            "previous_month_jobs": previous_month_jobs,
            "submissions_previous_month": submissions_previous_month,
        }

        subject = subject_template.render(context).strip()
        message = message_template.render(context)
        send_mail(
            subject,
            message,
            settings.JOB_FROM_EMAIL,
            ["jobs@python.org", "olivia@python.org"],
        )
