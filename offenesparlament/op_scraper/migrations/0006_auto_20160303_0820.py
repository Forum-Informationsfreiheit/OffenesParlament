# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0005_subscribedcontent_latest_content'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='debatestatement',
            name='debugdump',
        ),
        migrations.AddField(
            model_name='debatestatement',
            name='date_end',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='debatestatement',
            name='time_end',
            field=models.CharField(max_length=12, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='debatestatement',
            name='time_start',
            field=models.CharField(max_length=12, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='debatestatement',
            name='date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='content',
            field=models.ForeignKey(related_name='subscriptions', to='op_scraper.SubscribedContent'),
        ),
    ]
