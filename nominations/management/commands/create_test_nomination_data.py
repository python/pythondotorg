import datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from nominations.models import (
    Fellow,
    FellowNomination,
    FellowNominationRound,
    FellowNominationVote,
)
from users.models import User


class Command(BaseCommand):
    help = "Creates test nomination data for the nominations app (development only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force execution even in non-DEBUG mode (use with extreme caution)",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "This command cannot be run in production (DEBUG=False). "
                "This command creates test data and should only be used in development environments."
            )

        self._create_groups_and_users()
        self._create_rounds()
        self._create_nominations()
        self._create_votes()
        self._create_fellows()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created test nomination data: "
                f"{FellowNominationRound.objects.count()} rounds, "
                f"{FellowNomination.objects.count()} nominations, "
                f"{FellowNominationVote.objects.count()} votes, "
                f"{Fellow.objects.count()} fellows"
            )
        )

    # -- helpers ---------------------------------------------------------------

    def _get_or_create_user(self, username, first_name, last_name, email=None, is_staff=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "email": email or f"{username}@example.com",
                "is_staff": is_staff,
            },
        )
        if created:
            user.set_password("password")
            user.save()
            self.stdout.write(f"  Created user: {username}")
        return user

    def _get_or_create_round(self, year, quarter, is_open=True):
        quarter_dates = {
            1: (
                datetime.date(year, 1, 1),
                datetime.date(year, 3, 31),
                datetime.date(year, 2, 20),
                datetime.date(year, 3, 20),
            ),
            2: (
                datetime.date(year, 4, 1),
                datetime.date(year, 6, 30),
                datetime.date(year, 5, 20),
                datetime.date(year, 6, 20),
            ),
            3: (
                datetime.date(year, 7, 1),
                datetime.date(year, 9, 30),
                datetime.date(year, 8, 20),
                datetime.date(year, 9, 20),
            ),
            4: (
                datetime.date(year, 10, 1),
                datetime.date(year, 12, 31),
                datetime.date(year, 11, 20),
                datetime.date(year, 12, 20),
            ),
        }
        start, end, cutoff, review_end = quarter_dates[quarter]
        obj, created = FellowNominationRound.objects.get_or_create(
            year=year,
            quarter=quarter,
            defaults={
                "quarter_start": start,
                "quarter_end": end,
                "nominations_cutoff": cutoff,
                "review_start": cutoff,
                "review_end": review_end,
                "is_open": is_open,
            },
        )
        if created:
            self.stdout.write(f"  Created round: {obj}")
        return obj

    def _create_nomination(
        self,
        nominator,
        nominee_name,
        nominee_email,
        nomination_round,
        status="pending",
        expiry_round=None,
        nominee_user=None,
        nominee_is_fellow_at_submission=False,
    ):
        return FellowNomination.objects.create(
            nominator=nominator,
            nominee_name=nominee_name,
            nominee_email=nominee_email,
            nomination_statement=(f"{nominee_name} has made outstanding contributions to the Python community."),
            nomination_round=nomination_round,
            status=status,
            expiry_round=expiry_round,
            nominee_user=nominee_user,
            nominee_is_fellow_at_submission=nominee_is_fellow_at_submission,
        )

    def _get_or_create_fellow(self, name, year_elected, status="active", emeritus_year=None, notes="", user=None):
        obj, created = Fellow.objects.get_or_create(
            name=name,
            defaults={
                "year_elected": year_elected,
                "status": status,
                "emeritus_year": emeritus_year,
                "notes": notes,
                "user": user,
            },
        )
        if created:
            self.stdout.write(f"  Created fellow: {name}")
        return obj

    # -- data creation ---------------------------------------------------------

    def _create_groups_and_users(self):
        self.stdout.write("Creating groups and users...")

        self.wg_group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")

        self.wg_members = [
            self._get_or_create_user("wg_alice", "Alice", "WGMember", "alice.wg@python.org"),
            self._get_or_create_user("wg_bob", "Bob", "Reviewer", "bob.wg@python.org"),
            self._get_or_create_user("wg_carol", "Carol", "Evaluator", "carol.wg@python.org"),
            self._get_or_create_user("wg_dave", "Dave", "Assessor", "dave.wg@python.org"),
        ]
        for member in self.wg_members:
            member.groups.add(self.wg_group)

        self.staff_user = self._get_or_create_user("staff_admin", "Staff", "Admin", is_staff=True)
        self.nominator1 = self._get_or_create_user("nominator1", "Nominator", "One", "nominator1@example.com")
        self.nominator2 = self._get_or_create_user("nominator2", "Nominator", "Two", "nominator2@example.com")

    def _create_rounds(self):
        self.stdout.write("Creating nomination rounds...")

        self.past_round = self._get_or_create_round(2025, 3, is_open=False)
        self.current_round = self._get_or_create_round(2026, 1, is_open=True)
        self.future_round = self._get_or_create_round(2026, 2, is_open=False)
        self.expiry_round = self._get_or_create_round(2026, 4, is_open=False)
        self.old_expiry = self._get_or_create_round(2025, 2, is_open=False)

    def _create_nominations(self):
        self.stdout.write("Creating nominations...")

        # Past round (2025-Q3)
        self._create_nomination(
            self.nominator1,
            "Past Accepted One",
            "past1@example.com",
            self.past_round,
            status="accepted",
        )
        self._create_nomination(
            self.nominator2,
            "Past Accepted Two",
            "past2@example.com",
            self.past_round,
            status="accepted",
        )
        self._create_nomination(
            self.nominator1,
            "Past Not Accepted",
            "past_na@example.com",
            self.past_round,
            status="not_accepted",
        )

        # Current round (2026-Q1) — pending
        for nominator, name, email in [
            (self.nominator1, "Pending Person One", "pending1@example.com"),
            (self.nominator2, "Pending Person Two", "pending2@example.com"),
            (self.nominator1, "Pending Person Three", "pending3@example.com"),
        ]:
            self._create_nomination(
                nominator,
                name,
                email,
                self.current_round,
                status="pending",
                expiry_round=self.expiry_round,
            )

        # Current round — under_review (votes added separately)
        self.under_review_majority_yes = self._create_nomination(
            self.nominator1,
            "Review Majority Yes",
            "review_yes@example.com",
            self.current_round,
            status="under_review",
            expiry_round=self.expiry_round,
        )
        self.under_review_majority_no = self._create_nomination(
            self.nominator2,
            "Review Majority No",
            "review_no@example.com",
            self.current_round,
            status="under_review",
            expiry_round=self.expiry_round,
        )
        self.under_review_tie = self._create_nomination(
            self.nominator1,
            "Review Tie Vote",
            "review_tie@example.com",
            self.current_round,
            status="under_review",
            expiry_round=self.expiry_round,
        )
        self.under_review_abstains = self._create_nomination(
            self.nominator2,
            "Review All Abstain",
            "review_abstain@example.com",
            self.current_round,
            status="under_review",
            expiry_round=self.expiry_round,
        )
        self.under_review_one_vote = self._create_nomination(
            self.nominator1,
            "Review One Vote",
            "review_onevote@example.com",
            self.current_round,
            status="under_review",
            expiry_round=self.expiry_round,
        )

        # Current round — accepted
        self._create_nomination(
            self.nominator2,
            "Current Accepted",
            "current_accepted@example.com",
            self.current_round,
            status="accepted",
        )

        # Nominee who is already a Fellow
        fellow_nominee_user = self._get_or_create_user(
            "already_fellow", "Already", "Fellow", "already_fellow@example.com"
        )
        self._get_or_create_fellow("Already Fellow", 2020, user=fellow_nominee_user)
        self._create_nomination(
            self.nominator1,
            "Already Fellow",
            "already_fellow@example.com",
            self.current_round,
            status="pending",
            expiry_round=self.expiry_round,
            nominee_user=fellow_nominee_user,
            nominee_is_fellow_at_submission=True,
        )

        # Expired nomination (expiry_round in the past)
        self._create_nomination(
            self.nominator2,
            "Expired Pending",
            "expired@example.com",
            self.past_round,
            status="pending",
            expiry_round=self.old_expiry,
        )

        self.stdout.write(f"  Created {FellowNomination.objects.count()} nominations")

    def _create_votes(self):
        self.stdout.write("Creating votes...")
        wg1, wg2, wg3, wg4 = self.wg_members

        # Majority yes (3 yes, 1 no)
        for voter, vote, comment in [
            (wg1, "yes", "Strong contributor."),
            (wg2, "yes", "Agree."),
            (wg3, "yes", "Excellent candidate."),
            (wg4, "no", "Need more info."),
        ]:
            FellowNominationVote.objects.get_or_create(
                nomination=self.under_review_majority_yes,
                voter=voter,
                defaults={"vote": vote, "comment": comment},
            )

        # Majority no (1 yes, 2 no, 1 abstain)
        for voter, vote, comment in [
            (wg1, "yes", "Good work."),
            (wg2, "no", "Insufficient contributions."),
            (wg3, "no", "Not yet."),
            (wg4, "abstain", "Conflict of interest."),
        ]:
            FellowNominationVote.objects.get_or_create(
                nomination=self.under_review_majority_no,
                voter=voter,
                defaults={"vote": vote, "comment": comment},
            )

        # Tie (2 yes, 2 no)
        for voter, vote in [(wg1, "yes"), (wg2, "yes"), (wg3, "no"), (wg4, "no")]:
            FellowNominationVote.objects.get_or_create(
                nomination=self.under_review_tie,
                voter=voter,
                defaults={"vote": vote},
            )

        # All abstains
        for voter in self.wg_members:
            FellowNominationVote.objects.get_or_create(
                nomination=self.under_review_abstains,
                voter=voter,
                defaults={"vote": "abstain"},
            )

        # One vote cast
        FellowNominationVote.objects.get_or_create(
            nomination=self.under_review_one_vote,
            voter=wg1,
            defaults={"vote": "yes", "comment": "Looks promising."},
        )

        self.stdout.write(f"  Created {FellowNominationVote.objects.count()} votes")

    def _create_fellows(self):
        self.stdout.write("Creating fellow records for roster...")

        fellow_data = [
            ("guido_van_rossum", "Guido", "van Rossum", "guido@python.org", 2001),
            ("carol_willing", "Carol", "Willing", "carol@python.org", 2017),
            ("mariatta_wijaya", "Mariatta", "Wijaya", "mariatta@python.org", 2018),
            ("naomi_ceder", "Naomi", "Ceder", "naomi@python.org", 2015),
            ("victor_stinner", "Victor", "Stinner", "victor@python.org", 2016),
            ("brett_cannon", "Brett", "Cannon", "brett@python.org", 2010),
            ("barry_warsaw", "Barry", "Warsaw", "barry@python.org", 2009),
        ]
        for username, first, last, email, year in fellow_data:
            user = self._get_or_create_user(username, first, last, email)
            self._get_or_create_fellow(f"{first} {last}", year, user=user)

        # Emeritus and deceased examples for roster section testing
        self._get_or_create_fellow("Emeritus Example", 2005, status="emeritus", emeritus_year=2020)
        self._get_or_create_fellow("In Memoriam Example", 2003, status="deceased", notes="Remembered fondly.")
