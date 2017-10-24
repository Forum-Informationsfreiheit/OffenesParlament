# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0013_auto_20171020_1655'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='mandates',
        ),
        migrations.AddField(
            model_name='mandate',
            name='person',
            field=models.ForeignKey(default=0, to='op_scraper.Person'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='verification',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]
