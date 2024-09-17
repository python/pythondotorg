from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0005_job_other_job_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='region',
            field=models.CharField(blank=True, max_length=100, null=True),
            preserve_default=True,
        ),
    ]
