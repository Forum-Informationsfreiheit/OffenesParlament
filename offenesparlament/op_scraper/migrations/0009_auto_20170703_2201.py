# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0008_commentedcontent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commentedcontent',
            name='created_by_name',
        ),
        migrations.RemoveField(
            model_name='commentedcontent',
            name='image',
        ),
        migrations.AddField(
            model_name='commentedcontent',
            name='created_by_name',
            field=models.CharField(default=None, max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='commentedcontent',
            name='image',
            field=models.ImageField(null=True, upload_to=b''),
        ),
        migrations.AddField(
            model_name='commentedcontent',
            name='approved_by',
            field=models.ForeignKey(related_name='approved_content', to='op_scraper.User', null=True),
        ),
        migrations.AlterField(
            model_name='commentedcontent',
            name='title',
            field=models.CharField(max_length=240),
        ),
    ]
