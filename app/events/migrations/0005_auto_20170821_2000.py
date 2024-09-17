from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_auto_20170814_0519'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='categories',
            field=models.ManyToManyField(related_name='events', to='events.EventCategory', blank=True),
        ),
    ]
