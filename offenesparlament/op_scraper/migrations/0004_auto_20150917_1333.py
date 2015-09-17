# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0003_person_latest_mandate'),
    ]

    operations = [
        migrations.AddField(
            model_name='law',
            name='_slug',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='person',
            name='_slug',
            field=models.CharField(default=b'', max_length=255),
        ),
    ]
