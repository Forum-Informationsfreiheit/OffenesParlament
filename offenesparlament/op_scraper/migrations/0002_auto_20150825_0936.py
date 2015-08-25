# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='administration',
            name='end_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
