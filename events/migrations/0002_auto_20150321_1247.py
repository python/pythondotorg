from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='occurringrule',
            name='all_day',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='recurringrule',
            name='all_day',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
