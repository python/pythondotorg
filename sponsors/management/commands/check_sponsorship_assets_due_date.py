from datetime import timedelta

from django.core.management import BaseCommand
from django.db.models import Subquery
from django.utils import timezone

from sponsors.models import Sponsorship, Contract, BenefitFeature
from sponsors.notifications import AssetCloseToDueDateNotificationToSponsors


class Command(BaseCommand):
    """
    This command will query for the sponsorships which have any required asset
    with a due date expiring within the certain amount of days
    """
    help = "Send notifications to sponsorship with pending required assets"

    def add_arguments(self, parser):
        help = "Num of days to be used as interval up to target date"
        parser.add_argument("num_days", nargs="?", default="7", help=help)
        parser.add_argument("--no-input", action="store_true", help="Tells Django to NOT prompt the user for input of any kind.")

    def handle(self, **options):
        num_days = options["num_days"]
        ask_input = not options["no_input"]
        target_date = (timezone.now() + timedelta(days=int(num_days))).date()

        req_assets = BenefitFeature.objects.required_assets()

        sponsorship_ids = Subquery(req_assets.values_list("sponsor_benefit__sponsorship_id").distinct())
        sponsorships = Sponsorship.objects.filter(id__in=sponsorship_ids)

        sponsorships_to_notify = []
        for sponsorship in sponsorships:
            to_notify = any([
                asset.due_date == target_date
                for asset in req_assets.from_sponsorship(sponsorship)
                if asset.due_date
            ])
            if to_notify:
                sponsorships_to_notify.append(sponsorship)

        if not sponsorships_to_notify:
            print("No sponsorship with required assets with due date close to expiration.")
            return

        user_input = ""
        while user_input != "Y" and ask_input:
            msg = f"Contacts from {len(sponsorships_to_notify)} with pending assets with expiring due date will get " \
                  f"notified. "
            msg += "Do you want to proceed? [Y/n]: "
            user_input = input(msg).strip().upper()
            if user_input == "N":
                print("Finishing execution.")
                return
            elif user_input != "Y":
                print("Invalid option...")

        notification = AssetCloseToDueDateNotificationToSponsors()
        for sponsorship in sponsorships_to_notify:
            kwargs = {"sponsorship": sponsorship, "days": num_days, "due_date": target_date}
            notification.notify(**kwargs)

        print("Notifications sent!")
