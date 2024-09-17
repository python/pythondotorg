from django.db import models, migrations


def remove_job_submit_sidebar_box(apps, schema_editor):
    """
    Remove jobs-submitajob box
    """
    Box = apps.get_model('boxes', 'Box')
    try:
        submit_box = Box.objects.get(label='jobs-submitajob')
        submit_box.delete()
    except Box.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_auto_20150211_1634'),
        ('boxes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(remove_job_submit_sidebar_box),
    ]
