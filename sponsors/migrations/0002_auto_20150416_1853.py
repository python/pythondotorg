from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sponsors", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sponsor",
            name="content_markup_type",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("", "--"),
                    ("html", "HTML"),
                    ("plain", "Plain"),
                    ("markdown", "Markdown"),
                    ("restructuredtext", "Restructured Text"),
                ],
                default="restructuredtext",
                blank=True,
            ),
            preserve_default=True,
        ),
    ]
