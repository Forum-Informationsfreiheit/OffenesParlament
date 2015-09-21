# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0004_auto_20150917_1333'),
    ]

    operations = [
        migrations.AddField(
            model_name='keyword',
            name='_title_urlsafe',
            field=models.CharField(default=b'', max_length=255),
        ),
    ]
