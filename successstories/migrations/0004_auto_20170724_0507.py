from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('successstories', '0003_auto_20170720_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='company_url',
            field=models.URLField(verbose_name='Company URL'),
            preserve_default=True,
        ),
    ]
