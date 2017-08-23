# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0010_auto_20170710_0007'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentedcontent',
            name='admin_notification_sent',
            field=models.BooleanField(default=False),
        ),
    ]
