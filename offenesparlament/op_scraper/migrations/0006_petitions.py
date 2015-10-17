# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0005_keyword__title_urlsafe'),
    ]

    operations = [
        migrations.CreateModel(
            name='Petition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('signable', models.BooleanField()),
                ('signing_url', models.URLField(default=b'', max_length=255)),
                ('signature_count', models.IntegerField(default=0)),
                ('law', models.OneToOneField(related_name='petition', to='op_scraper.Law')),
                ('reference', models.OneToOneField(related_name='redistribution', null=True, blank=True, to='op_scraper.Petition')),
            ],
        ),
        migrations.CreateModel(
            name='PetitionCreator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(max_length=255)),
                ('created_petitions', models.ManyToManyField(related_name='creators', to='op_scraper.Petition')),
                ('person', models.OneToOneField(related_name='petitions_created', null=True, to='op_scraper.Person')),
            ],
        ),
        migrations.AlterModelOptions(
            name='opinion',
            options={'ordering': ['date']},
        ),
    ]
