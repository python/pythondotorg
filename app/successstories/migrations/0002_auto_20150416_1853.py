from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('successstories', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='content_markup_type',
            field=models.CharField(max_length=30, default='restructuredtext', choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')]),
            preserve_default=True,
        ),
    ]
