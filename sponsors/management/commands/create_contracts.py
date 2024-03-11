from django.core.management import BaseCommand

from sponsors.models import Sponsorship, Contract

# The reason to not use a data migration but a django management command
# to deal with pre existing approved Sponsorships is due to migrations
# limitations. A new Contract for a Sponsorship is created by the Contract's new
# classmethod. This method operates directly in top of other models such as
# SponsorBenefits and LegalClauses to organize the contract's information.
# A data migration would have to re-implement the same logic since the migration,
# when running, doesn't have access to user defined methods in the models.
# The same limitation is true for the SponsorshipQuerySet's approved method and for
# the sponsorship.contract reverse lookup.

class Command(BaseCommand):
    """
    Create Contract objects for existing approved Sponsorships.

    Run this command as a initial data migration or to make sure
    all approved Sponsorships do have associated Contract objects.
    """
    help = "Create Contract objects for existing approved Sponsorships."

    def handle(self, **options):
        qs = Sponsorship.objects.approved().filter(contract__isnull=True)
        if not qs.exists():
            print("There's no approved Sponsorship without associated Contract. Terminating.")
            return

        print(f"Creating contract for {qs.count()} approved sponsorships...")
        for sponsorship in qs:
            Contract.new(sponsorship)

        print(f"Done!")
