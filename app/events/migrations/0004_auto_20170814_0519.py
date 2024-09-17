from django.db import migrations, models

from app.events.models import duration_default


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_auto_20150416_1853'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringrule',
            name='duration_internal',
            field=models.DurationField(default=duration_default),
        ),
        migrations.AlterField(
            model_name='recurringrule',
            name='duration',
            field=models.CharField(default='15 min', max_length=50),
        ),
    ]
