# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0003_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscribedcontent',
            name='latest_content_hashes',
            field=models.TextField(null=True, blank=True),
        ),
    ]
