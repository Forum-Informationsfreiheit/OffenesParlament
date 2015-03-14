# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='html_link',
            field=models.URLField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='pdf_link',
            field=models.URLField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='stripped_html',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
    ]
