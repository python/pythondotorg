from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0007_auto_20150227_2223'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobcategory',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='jobtype',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='region',
            field=models.CharField(blank=True, verbose_name='State, Province or Region', max_length=100, default=''),
            preserve_default=False,
        ),
    ]
