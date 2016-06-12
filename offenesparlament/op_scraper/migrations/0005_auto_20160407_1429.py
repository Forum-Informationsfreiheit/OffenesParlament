# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0004_debate__slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='latest_mandate',
            field=models.ForeignKey(related_name='latest_mandate', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='op_scraper.Mandate', null=True),
        ),
    ]
