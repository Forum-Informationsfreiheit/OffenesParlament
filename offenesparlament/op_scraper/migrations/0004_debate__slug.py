# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0003_subscribedcontent_ui_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='debate',
            name='_slug',
            field=models.CharField(default=b'', max_length=255),
        ),
    ]
