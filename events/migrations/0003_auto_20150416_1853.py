from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_auto_20150321_1247'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='description_markup_type',
            field=models.CharField(max_length=30, default='restructuredtext', choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')]),
            preserve_default=True,
        ),
    ]
