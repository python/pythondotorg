from django.db import models, migrations
import markupfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='description',
            field=markupfield.fields.MarkupField(rendered_field=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='description_markup_type',
            field=models.CharField(choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], max_length=30, default='restructuredtext'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='requirements',
            field=markupfield.fields.MarkupField(rendered_field=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='requirements_markup_type',
            field=models.CharField(choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], max_length=30, default='restructuredtext'),
            preserve_default=True,
        ),
    ]
