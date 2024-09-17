from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0006_region_nullable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='dt_end',
        ),
        migrations.RemoveField(
            model_name='job',
            name='dt_start',
        ),
        migrations.AddField(
            model_name='job',
            name='expires',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Job Listing Expiration Date'),
            preserve_default=True,
        ),
    ]
