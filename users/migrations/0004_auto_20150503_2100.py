from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20150503_2026'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='membership_type',
            field=models.IntegerField(choices=[(0, 'Basic Member'), (1, 'Supporting Member'), (2, 'Sponsor Member'), (3, 'Managing Member'), (4, 'Contributing Member'), (5, 'Fellow')], default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='membership',
            name='votes',
            field=models.BooleanField(verbose_name='I would like to be a PSF Voting Member', default=False),
            preserve_default=True,
        ),
    ]
