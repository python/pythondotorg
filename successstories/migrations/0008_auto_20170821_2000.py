# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('successstories', '0007_remove_story_weight'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='name',
            field=models.CharField(max_length=200),
        ),
    ]
