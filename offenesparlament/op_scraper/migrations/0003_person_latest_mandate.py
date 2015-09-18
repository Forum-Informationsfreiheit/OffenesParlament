# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0002_auto_20150825_0936'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='latest_mandate',
            field=models.ForeignKey(related_name='latest_mandate', blank=True, to='op_scraper.Mandate', null=True),
        ),
    ]
