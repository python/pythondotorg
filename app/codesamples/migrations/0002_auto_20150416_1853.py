from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('codesamples', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='codesample',
            name='code_markup_type',
            field=models.CharField(max_length=30, choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')], default='html', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='codesample',
            name='copy_markup_type',
            field=models.CharField(max_length=30, choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')], default='html', blank=True),
            preserve_default=True,
        ),
    ]
