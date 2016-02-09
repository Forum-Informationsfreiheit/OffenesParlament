# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0004_auto_20160202_1724'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscribedcontent',
            name='latest_content',
            field=models.TextField(null=True, blank=True),
        ),
    ]
