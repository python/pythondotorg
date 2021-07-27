from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_auto_20150211_1738'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='company',
        ),
        migrations.AlterField(
            model_name='job',
            name='company_name',
            field=models.CharField(null=True, max_length=100),
            preserve_default=True,
        ),
    ]
