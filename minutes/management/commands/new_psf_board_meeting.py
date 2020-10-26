from datetime import datetime

from django.core.management.base import BaseCommand

from minutes.meetings_factories import new_psf_board_meeting


class Command(BaseCommand):
    """ CLI to create a PSF board meeting """

    def add_arguments(self, parser):
        parser.add_argument("date")

    def clean_date(self, date):
        return datetime.strptime(date, "%Y-%m-%d").date()

    def handle(self, *args, **kwargs):
        date = self.clean_date(kwargs["date"])
        meeting = new_psf_board_meeting(date)
