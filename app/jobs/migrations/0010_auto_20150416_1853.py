from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0009_auto_20150317_1815'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='company_description_markup_type',
            field=models.CharField(max_length=30, choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')], default='restructuredtext', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='description_markup_type',
            field=models.CharField(max_length=30, default='restructuredtext', choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='requirements_markup_type',
            field=models.CharField(max_length=30, default='restructuredtext', choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')]),
            preserve_default=True,
        ),
    ]
