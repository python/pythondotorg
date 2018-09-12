# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('downloads', '0003_auto_20150824_1612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='_content_rendered',
            field=models.TextField(editable=False, default=''),
        ),
    ]
