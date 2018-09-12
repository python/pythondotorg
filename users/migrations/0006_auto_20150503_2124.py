# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_public_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='creator',
            field=models.OneToOneField(null=True, blank=True, to=settings.AUTH_USER_MODEL, related_name='membership', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
