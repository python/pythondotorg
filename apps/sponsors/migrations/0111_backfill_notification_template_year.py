from django.db import migrations

from apps.sponsors.models.notifications import year_from_name


def backfill_year(apps, schema_editor):
    SponsorEmailNotificationTemplate = apps.get_model("sponsors", "SponsorEmailNotificationTemplate")
    for template in SponsorEmailNotificationTemplate.objects.filter(year__isnull=True):
        year = year_from_name(template.internal_name)
        if year is not None:
            template.year = year
            template.save(update_fields=["year"])


def noop_reverse(apps, schema_editor):
    """Leave the backfilled years in place; there is nothing to reconstruct from on reverse."""


class Migration(migrations.Migration):
    dependencies = [
        ("sponsors", "0110_notification_template_year_and_log_fk"),
    ]

    operations = [migrations.RunPython(backfill_year, noop_reverse)]
