# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0002_person_photo_copyright'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegislativePeriod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField()),
                ('roman_numeral', models.CharField(max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True, blank=True)),
            ],
        ),
    ]
