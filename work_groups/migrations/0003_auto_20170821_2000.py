from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('work_groups', '0002_auto_20150604_2203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workgroup',
            name='support_markup_type',
            field=models.CharField(choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')], default='restructuredtext', max_length=30),
        ),
    ]
