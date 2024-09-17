from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0012_auto_20170809_1849'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='jobreviewcomment',
            options={'ordering': ('created',)},
        ),
    ]
