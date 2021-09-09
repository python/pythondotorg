from django.db import models, migrations
import markupfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("companies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Sponsor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        auto_created=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, blank=True
                    ),
                ),
                (
                    "updated",
                    models.DateTimeField(default=django.utils.timezone.now, blank=True),
                ),
                (
                    "content",
                    markupfield.fields.MarkupField(rendered_field=True, blank=True),
                ),
                (
                    "content_markup_type",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("", "--"),
                            ("html", "html"),
                            ("plain", "plain"),
                            ("markdown", "markdown"),
                            ("restructuredtext", "restructuredtext"),
                        ],
                        default="restructuredtext",
                        blank=True,
                    ),
                ),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                (
                    "featured",
                    models.BooleanField(
                        help_text="Check to include Sponsor in feature rotation",
                        db_index=True,
                        default=False,
                    ),
                ),
                ("_content_rendered", models.TextField(editable=False)),
                (
                    "company",
                    models.ForeignKey(to="companies.Company", on_delete=models.CASCADE),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        null=True,
                        to=settings.AUTH_USER_MODEL,
                        related_name="sponsors_sponsor_creator",
                        blank=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "last_modified_by",
                    models.ForeignKey(
                        null=True,
                        to=settings.AUTH_USER_MODEL,
                        related_name="sponsors_sponsor_modified",
                        blank=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "sponsor",
                "verbose_name_plural": "sponsors",
            },
            bases=(models.Model,),
        ),
    ]
