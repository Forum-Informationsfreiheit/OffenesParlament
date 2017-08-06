# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0007_auto_20170529_1619'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentedContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_by_name', models.TextField()),
                ('image', models.ImageField(upload_to=b'')),
                ('title', models.TextField()),
                ('body', models.TextField()),
                ('created_by', models.ForeignKey(to='op_scraper.User')),
            ],
        ),
    ]
