from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20150503_2100'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='public_profile',
            field=models.BooleanField(verbose_name='Make my profile public', default=True),
            preserve_default=True,
        ),
    ]
