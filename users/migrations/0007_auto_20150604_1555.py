from django.db import models, migrations


def create_psf_membership_flag(apps, schema_editor):
    Flag = apps.get_model('waffle', 'Flag')
    Flag.objects.create(
        name='psf_membership',
        testing=True,
        note='This flag is used to show the PSF Basic and Advanced member registration process.'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20150503_2124'),
        ('waffle', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_psf_membership_flag),
    ]
