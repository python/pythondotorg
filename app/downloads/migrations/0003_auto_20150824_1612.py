from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('downloads', '0002_auto_20150416_1853'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='version',
            field=models.IntegerField(default=3, choices=[(3, 'Python 3.x.x'), (2, 'Python 2.x.x'), (1, 'Python 1.x.x')]),
            preserve_default=True,
        ),
    ]
