# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscribedcontent',
            name='latest_content_hash',
        ),
        migrations.AddField(
            model_name='subscribedcontent',
            name='latest_content_hashes',
            field=models.TextField(max_length=16, null=True, blank=True),
        ),
    ]
