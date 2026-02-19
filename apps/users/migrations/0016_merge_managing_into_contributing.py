# Data migration: Merge MANAGING (3) membership_type into CONTRIBUTING (4)
# Per 2024 PSF Bylaws Change 1 (https://github.com/psf/bylaws/pull/4)

from django.db import migrations


def merge_managing_into_contributing(apps, schema_editor):
    Membership = apps.get_model("users", "Membership")
    Membership.objects.filter(membership_type=3).update(membership_type=4)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0015_alter_user_first_name"),
    ]

    operations = [
        migrations.RunPython(
            merge_managing_into_contributing,
            migrations.RunPython.noop,
        ),
    ]
