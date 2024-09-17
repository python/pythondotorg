from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('work_groups', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workgroup',
            name='url',
            field=models.URLField(help_text='Main URL for Group', verbose_name='URL', blank=True),
            preserve_default=True,
        ),
    ]
