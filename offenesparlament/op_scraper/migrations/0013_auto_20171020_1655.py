# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0012_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='verification',
            name='created_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='commentedcontent',
            name='created_by_link',
            field=models.URLField(max_length=250, verbose_name=b'Website des Autors', blank=True),
        ),
    ]
