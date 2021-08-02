from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('successstories', '0002_auto_20150416_1853'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='author_email',
            field=models.EmailField(blank=True, max_length=100, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='story',
            name='author',
            field=models.CharField(max_length=500, help_text='Author of the content'),
            preserve_default=True,
        ),
    ]
