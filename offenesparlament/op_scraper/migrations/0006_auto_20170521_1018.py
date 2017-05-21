# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0005_auto_20160407_1429'),
    ]

    operations = [
        migrations.AlterField(
            model_name='step',
            name='title',
            field=models.TextField(),
        ),
    ]
