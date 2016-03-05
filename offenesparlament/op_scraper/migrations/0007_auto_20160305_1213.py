# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0006_auto_20160303_0820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statement',
            name='protocol_url',
            field=models.URLField(default=b'', max_length=255, null=True),
        ),
    ]
