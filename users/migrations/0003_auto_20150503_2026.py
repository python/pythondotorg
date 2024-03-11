from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20150416_1853'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='last_vote_affirmation',
            field=models.DateTimeField(blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='membership',
            name='votes',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
