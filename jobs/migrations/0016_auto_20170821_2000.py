from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0015_auto_20170814_0301'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='company_description_markup_type',
            field=models.CharField(choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')], default='restructuredtext', max_length=30),
        ),
    ]
