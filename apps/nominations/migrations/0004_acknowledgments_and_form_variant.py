from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nominations", "0003_election_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="electionkind",
            name="nomination_form",
            field=models.CharField(
                choices=[("board", "PSF Board"), ("packaging_council", "Packaging Council")],
                default="board",
                help_text="Which nomination form and acknowledgment wording elections of this kind use.",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="election",
            name="hide_previous_service",
            field=models.BooleanField(
                default=False,
                help_text="Hide the 'previous service' field on the nomination form (e.g. an inaugural election with no prior terms).",
            ),
        ),
        migrations.AddField(
            model_name="nomination",
            name="coc_acknowledged",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="nomination",
            name="mission_alignment",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="nomination",
            name="eligibility_confirmed",
            field=models.BooleanField(default=False),
        ),
    ]
