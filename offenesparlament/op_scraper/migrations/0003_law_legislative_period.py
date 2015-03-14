# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0002_auto_20150314_1243'),
    ]

    operations = [
        migrations.AddField(
            model_name='law',
            name='legislative_period',
            field=models.IntegerField(default=1),
            preserve_default=True,
        ),
    ]
