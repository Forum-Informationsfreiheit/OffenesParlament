# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0004_auto_20150314_1403'),
    ]

    operations = [
        migrations.AlterField(
            model_name='law',
            name='parl_id',
            field=models.CharField(default=b'', max_length=30),
            preserve_default=True,
        ),
    ]
