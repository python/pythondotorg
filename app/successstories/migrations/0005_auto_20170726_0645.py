from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('successstories', '0004_auto_20170724_0507'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='name',
            field=models.CharField(max_length=200, help_text='Title of your success story'),
            preserve_default=True,
        ),
    ]
