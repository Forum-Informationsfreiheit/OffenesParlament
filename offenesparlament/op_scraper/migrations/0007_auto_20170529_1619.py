# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0006_auto_20170521_1018'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='step',
            options={'ordering': ['sortkey']},
        ),
    ]
