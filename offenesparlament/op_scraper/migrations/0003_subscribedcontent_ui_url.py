# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0002_subscribedcontent_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscribedcontent',
            name='ui_url',
            field=models.URLField(max_length=255, null=True, blank=True),
        ),
    ]
