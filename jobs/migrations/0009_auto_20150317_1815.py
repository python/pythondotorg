from django.db import models, migrations
import markupfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0008_auto_20150316_1205'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='agencies',
            field=models.BooleanField(verbose_name='Agencies are OK to contact?', default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='contact',
            field=models.CharField(verbose_name='Contact name', blank=True, null=True, max_length=100),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='description',
            field=markupfield.fields.MarkupField(verbose_name='Job description', rendered_field=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='email',
            field=models.EmailField(verbose_name='Contact email', max_length=75),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='other_job_type',
            field=models.CharField(verbose_name='Other job technologies', blank=True, max_length=100),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='requirements',
            field=markupfield.fields.MarkupField(verbose_name='Job requirements', rendered_field=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='telecommuting',
            field=models.BooleanField(verbose_name='Telecommuting allowed?', default=False),
            preserve_default=True,
        ),
    ]
