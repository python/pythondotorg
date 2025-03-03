# Generated by Django 4.2.11 on 2024-09-05 17:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sponsors', '0102_auto_20240509_2037'),
    ]

    operations = [
        migrations.AlterField(
            model_name='benefitfeature',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='benefitfeatureconfiguration',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='genericasset',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='sponsor',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sponsor',
            name='last_modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sponsorshipbenefit',
            name='conflicts',
            field=models.ManyToManyField(blank=True, help_text='For benefits that conflict with one another,', to='sponsors.sponsorshipbenefit', verbose_name='Conflicts'),
        ),
    ]
