from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_auto_20150216_1544'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='other_job_type',
            field=models.CharField(max_length=100, verbose_name='Other Job Technologies', blank=True),
            preserve_default=True,
        ),
    ]
