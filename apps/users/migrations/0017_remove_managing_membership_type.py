from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0016_merge_managing_into_contributing"),
    ]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="membership_type",
            field=models.IntegerField(
                choices=[
                    (0, "Basic Member"),
                    (1, "Supporting Member"),
                    (2, "Sponsor Member"),
                    (4, "Contributing Member"),
                    (5, "Fellow"),
                ],
                default=0,
            ),
        ),
    ]
