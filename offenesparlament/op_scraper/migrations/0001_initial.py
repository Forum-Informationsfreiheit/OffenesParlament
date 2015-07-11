# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import phonenumber_field.modelfields
import op_scraper.models
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('pdf_link', models.URLField(null=True)),
                ('html_link', models.URLField(null=True)),
                ('stripped_html', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('title_detail', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Function',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Law',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('status', models.TextField(null=True, blank=True)),
                ('source_link', models.URLField(default=b'')),
                ('parl_id', models.CharField(default=b'', max_length=30)),
                ('description', models.TextField(blank=True)),
                ('category', models.ForeignKey(blank=True, to='op_scraper.Category', null=True)),
                ('documents', models.ManyToManyField(related_name='laws', to='op_scraper.Document')),
                ('keywords', models.ManyToManyField(related_name='laws', to='op_scraper.Keyword')),
            ],
            bases=(models.Model, op_scraper.models.ParlIDMixIn),
        ),
        migrations.CreateModel(
            name='LegislativePeriod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField()),
                ('roman_numeral', models.CharField(default=b'', unique=True, max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Mandate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True, blank=True)),
                ('function', models.ForeignKey(to='op_scraper.Function')),
            ],
        ),
        migrations.CreateModel(
            name='Opinion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('parl_id', models.CharField(default=b'', unique=True, max_length=30)),
                ('date', models.DateField(null=True)),
                ('description', models.TextField(blank=True)),
                ('source_link', models.URLField(default=b'')),
                ('category', models.ForeignKey(blank=True, to='op_scraper.Category', null=True)),
                ('documents', models.ManyToManyField(to='op_scraper.Document')),
                ('entity', models.ForeignKey(related_name='opinions', to='op_scraper.Entity')),
                ('keywords', models.ManyToManyField(to='op_scraper.Keyword')),
                ('prelaw', models.ForeignKey(related_name='opinions', to='op_scraper.Law')),
            ],
            bases=(models.Model, op_scraper.models.ParlIDMixIn),
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('titles', annoying.fields.JSONField(default=[], null=True, blank=True)),
                ('short', models.CharField(unique=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('parl_id', models.CharField(max_length=30, serialize=False, primary_key=True)),
                ('source_link', models.URLField(default=b'')),
                ('photo_link', models.URLField(default=b'')),
                ('photo_copyright', models.CharField(default=b'', max_length=255)),
                ('full_name', models.CharField(max_length=255)),
                ('reversed_name', models.CharField(max_length=255)),
                ('birthdate', models.DateField(null=True, blank=True)),
                ('birthplace', models.CharField(max_length=255, null=True, blank=True)),
                ('deathdate', models.DateField(null=True, blank=True)),
                ('deathplace', models.CharField(max_length=255, null=True, blank=True)),
                ('occupation', models.CharField(max_length=255, null=True, blank=True)),
                ('mandates', models.ManyToManyField(to='op_scraper.Mandate')),
                ('party', models.ForeignKey(to='op_scraper.Party')),
            ],
            bases=(models.Model, op_scraper.models.ParlIDMixIn),
        ),
        migrations.CreateModel(
            name='Phase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='PressRelease',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('subtitle', models.CharField(max_length=255)),
                ('full_text', models.TextField()),
                ('release_date', models.DateField()),
                ('source_link', models.URLField(default=b'')),
                ('parl_id', models.CharField(default=b'', unique=True, max_length=30)),
                ('topics', models.CharField(max_length=255)),
                ('format', models.CharField(max_length=255)),
                ('tags', models.CharField(max_length=255)),
            ],
            bases=(models.Model, op_scraper.models.ParlIDMixIn),
        ),
        migrations.CreateModel(
            name='Statement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('speech_type', models.CharField(max_length=255)),
                ('protocol_url', models.URLField(default=b'')),
                ('index', models.IntegerField(default=1)),
                ('person', models.ForeignKey(related_name='statements', to='op_scraper.Person')),
            ],
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('sortkey', models.CharField(max_length=6)),
                ('date', models.DateField()),
                ('protocol_url', models.URLField(default=b'')),
                ('source_link', models.URLField(default=b'')),
                ('law', models.ForeignKey(related_name='steps', blank=True, to='op_scraper.Law', null=True)),
                ('opinion', models.ForeignKey(related_name='steps', blank=True, to='op_scraper.Opinion', null=True)),
                ('phase', models.ForeignKey(to='op_scraper.Phase')),
            ],
        ),
        migrations.AddField(
            model_name='statement',
            name='step',
            field=models.ForeignKey(related_name='statements', to='op_scraper.Step'),
        ),
        migrations.AddField(
            model_name='mandate',
            name='party',
            field=models.ForeignKey(blank=True, to='op_scraper.Party', null=True),
        ),
        migrations.AddField(
            model_name='law',
            name='legislative_period',
            field=models.ForeignKey(to='op_scraper.LegislativePeriod'),
        ),
        migrations.AddField(
            model_name='law',
            name='press_releases',
            field=models.ManyToManyField(related_name='laws', to='op_scraper.PressRelease'),
        ),
        migrations.AddField(
            model_name='law',
            name='references',
            field=models.OneToOneField(related_name='laws', null=True, blank=True, to='op_scraper.Law'),
        ),
        migrations.AlterUniqueTogether(
            name='entity',
            unique_together=set([('title', 'title_detail')]),
        ),
        migrations.AlterUniqueTogether(
            name='law',
            unique_together=set([('parl_id', 'legislative_period')]),
        ),
    ]
