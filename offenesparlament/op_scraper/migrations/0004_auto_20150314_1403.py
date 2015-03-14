# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0003_law_legislative_period'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='law',
            unique_together=set([('parl_id', 'legislative_period')]),
        ),
    ]
