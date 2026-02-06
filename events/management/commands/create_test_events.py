from dateutil.rrule import DAILY, MONTHLY, WEEKLY
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from events.models import Calendar, Event, EventCategory, EventLocation, OccurringRule, RecurringRule


class Command(BaseCommand):
    help = "Creates test events for the events app (development only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force execution even in non-DEBUG mode (use with extreme caution)",
        )

    def handle(self, *args, **options):
        # Production safety check
        if not settings.DEBUG and not options["force"]:
            msg = "This command cannot be run in production (DEBUG=False). This command creates test data and should only be used in development environments."
            raise CommandError(msg)
        # Create main calendar
        main_calendar, created = Calendar.objects.get_or_create(
            slug="python-events",
            defaults={
                "name": "Python Events",
                "description": "Main Python community events calendar",
            },
        )
        self.stdout.write(f"Main calendar {'created' if created else 'already exists'}: {main_calendar}")

        # Create additional calendars
        user_group_calendar, _ = Calendar.objects.get_or_create(
            slug="user-group-events",
            defaults={
                "name": "User Group Events",
                "description": "Python user group meetups and events",
            },
        )

        conference_calendar, _ = Calendar.objects.get_or_create(
            slug="conferences",
            defaults={
                "name": "Python Conferences",
                "description": "Major Python conferences worldwide",
            },
        )

        # Create categories
        meetup_category, _ = EventCategory.objects.get_or_create(
            slug="meetup", calendar=main_calendar, defaults={"name": "Meetup"}
        )

        conference_category, _ = EventCategory.objects.get_or_create(
            slug="conference", calendar=main_calendar, defaults={"name": "Conference"}
        )

        workshop_category, _ = EventCategory.objects.get_or_create(
            slug="workshop", calendar=main_calendar, defaults={"name": "Workshop"}
        )

        sprint_category, _ = EventCategory.objects.get_or_create(
            slug="sprint", calendar=main_calendar, defaults={"name": "Sprint"}
        )

        # Create locations
        location_sf, _ = EventLocation.objects.get_or_create(
            name="San Francisco Python Meetup Space",
            calendar=main_calendar,
            defaults={"address": "123 Market St, San Francisco, CA 94105", "url": "https://example.com/sf-venue"},
        )

        location_ny, _ = EventLocation.objects.get_or_create(
            name="NYC Python Center",
            calendar=main_calendar,
            defaults={"address": "456 Broadway, New York, NY 10013", "url": "https://example.com/ny-venue"},
        )

        location_london, _ = EventLocation.objects.get_or_create(
            name="London Tech Hub",
            calendar=main_calendar,
            defaults={"address": "789 Oxford Street, London, UK", "url": "https://example.com/london-venue"},
        )

        location_online, _ = EventLocation.objects.get_or_create(
            name="Online", calendar=main_calendar, defaults={"address": "", "url": "https://zoom.us"}
        )

        # Current time reference
        now = timezone.now()

        # Create past, current, and future events

        # 1. Past conference (3 months ago)
        past_event = Event.objects.create(
            title="PyCon US 2024",
            calendar=conference_calendar,
            description="The largest annual gathering for the Python community.",
            venue=location_sf,
            featured=True,
        )
        past_event.categories.add(conference_category)
        OccurringRule.objects.create(
            event=past_event, dt_start=now - timezone.timedelta(days=90), dt_end=now - timezone.timedelta(days=87)
        )

        # 2. Ongoing workshop series (weekly)
        workshop_event = Event.objects.create(
            title="Python for Data Science Workshop",
            calendar=main_calendar,
            description="Weekly hands-on workshop covering pandas, numpy, and data visualization.",
            venue=location_online,
        )
        workshop_event.categories.add(workshop_category)
        RecurringRule.objects.create(
            event=workshop_event,
            begin=now - timezone.timedelta(days=30),
            finish=now + timezone.timedelta(days=90),
            duration="2 hours",
            interval=1,
            frequency=WEEKLY,
        )

        # 3. Monthly user group meetup
        meetup_event = Event.objects.create(
            title="NYC Python Meetup",
            calendar=user_group_calendar,
            description="Monthly gathering of Python enthusiasts in New York City. Lightning talks and networking.",
            venue=location_ny,
        )
        meetup_event.categories.add(meetup_category)
        RecurringRule.objects.create(
            event=meetup_event,
            begin=now - timezone.timedelta(days=60),
            finish=now + timezone.timedelta(days=365),
            duration="3 hours",
            interval=1,
            frequency=MONTHLY,
        )

        # 4. Upcoming sprint (next week)
        sprint_event = Event.objects.create(
            title="Django Sprint Weekend",
            calendar=main_calendar,
            description="Two-day sprint to contribute to Django core and ecosystem packages.",
            venue=location_sf,
        )
        sprint_event.categories.add(sprint_category)
        OccurringRule.objects.create(
            event=sprint_event, dt_start=now + timezone.timedelta(days=7), dt_end=now + timezone.timedelta(days=9)
        )

        # 5. Major upcoming conference
        pycon_europe = Event.objects.create(
            title="EuroPython 2025",
            calendar=conference_calendar,
            description="The official European Python conference bringing together Python users from across Europe and beyond.",
            venue=location_london,
            featured=True,
        )
        pycon_europe.categories.add(conference_category)
        OccurringRule.objects.create(
            event=pycon_europe, dt_start=now + timezone.timedelta(days=120), dt_end=now + timezone.timedelta(days=125)
        )

        # 6. Daily coding challenge (for next 30 days)
        daily_challenge = Event.objects.create(
            title="Python Daily Coding Challenge",
            calendar=main_calendar,
            description="Solve a new Python coding challenge every day. Perfect for interview prep!",
            venue=location_online,
        )
        daily_challenge.categories.add(workshop_category)
        RecurringRule.objects.create(
            event=daily_challenge,
            begin=now,
            finish=now + timezone.timedelta(days=30),
            duration="1 hour",
            interval=1,
            frequency=DAILY,
        )

        # 7. London Python meetup (monthly)
        london_meetup = Event.objects.create(
            title="London Python User Group",
            calendar=user_group_calendar,
            description="Monthly meetup for Pythonistas in London. Talks, tutorials, and pub discussions.",
            venue=location_london,
        )
        london_meetup.categories.add(meetup_category)
        RecurringRule.objects.create(
            event=london_meetup,
            begin=now - timezone.timedelta(days=45),
            finish=now + timezone.timedelta(days=180),
            duration="2 hours 30 min",
            interval=1,
            frequency=MONTHLY,
        )

        # 8. Annual Python conference
        pydata_global = Event.objects.create(
            title="PyData Global Conference",
            calendar=conference_calendar,
            description="The global conference on data science, machine learning, and AI with Python.",
            venue=location_online,
            featured=True,
        )
        pydata_global.categories.add(conference_category)
        OccurringRule.objects.create(
            event=pydata_global,
            dt_start=now + timezone.timedelta(days=60),
            dt_end=now + timezone.timedelta(days=63),
            all_day=True,
        )

        # 9. Weekend workshop
        ml_workshop = Event.objects.create(
            title="Machine Learning with Python: From Zero to Hero",
            calendar=main_calendar,
            description="Intensive weekend workshop covering ML fundamentals with scikit-learn and TensorFlow.",
            venue=location_sf,
        )
        ml_workshop.categories.add(workshop_category)
        OccurringRule.objects.create(
            event=ml_workshop, dt_start=now + timezone.timedelta(days=14), dt_end=now + timezone.timedelta(days=16)
        )

        # 10. Recurring online office hours
        office_hours = Event.objects.create(
            title="Python Core Dev Office Hours",
            calendar=main_calendar,
            description="Weekly office hours with Python core developers. Get your questions answered!",
            venue=location_online,
        )
        RecurringRule.objects.create(
            event=office_hours,
            begin=now - timezone.timedelta(days=14),
            finish=now + timezone.timedelta(days=90),
            duration="1 hour",
            interval=1,
            frequency=WEEKLY,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created test events across {Calendar.objects.count()} calendars")
        )
        self.stdout.write(f"Total events: {Event.objects.count()}")
        self.stdout.write(f"Featured events: {Event.objects.filter(featured=True).count()}")
        self.stdout.write(
            f"Events with recurring rules: {Event.objects.filter(recurring_rules__isnull=False).distinct().count()}"
        )
        self.stdout.write(
            f"Events with single occurrences: {Event.objects.filter(occurring_rule__isnull=False).count()}"
        )
