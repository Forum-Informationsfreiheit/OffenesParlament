# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import phonenumber_field.modelfields


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
            options={
            },
            bases=(models.Model,),
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
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=75)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Law',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('status', models.TextField(null=True, blank=True)),
                ('source_link', models.URLField(default=b'')),
                ('parl_id', models.CharField(default=b'', max_length=30)),
                ('legislative_period', models.IntegerField(default=1)),
                ('description', models.TextField(blank=True)),
                ('category', models.ForeignKey(blank=True, to='op_scraper.Category', null=True)),
                ('documents', models.ManyToManyField(related_name='laws', to='op_scraper.Document')),
                ('keywords', models.ManyToManyField(related_name='laws', to='op_scraper.Keyword')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Opinion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('parl_id', models.CharField(default=b'', unique=True, max_length=30)),
                ('date', models.DateField()),
                ('description', models.TextField(blank=True)),
                ('category', models.ForeignKey(blank=True, to='op_scraper.Category', null=True)),
                ('documents', models.ManyToManyField(to='op_scraper.Document')),
                ('entity', models.ForeignKey(to='op_scraper.Entity')),
                ('keywords', models.ManyToManyField(to='op_scraper.Keyword')),
                ('prelaw', models.ForeignKey(to='op_scraper.Law')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Phase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
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
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('sortkey', models.CharField(max_length=6)),
                ('date', models.DateField()),
                ('protocol_url', models.URLField(default=b'')),
                ('law', models.ForeignKey(related_name='steps', to='op_scraper.Law')),
                ('phase', models.ForeignKey(to='op_scraper.Phase')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='opinion',
            name='steps',
            field=models.ManyToManyField(to='op_scraper.Step'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='law',
            name='press_releases',
            field=models.ManyToManyField(related_name='laws', to='op_scraper.PressRelease'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='law',
            name='references',
            field=models.OneToOneField(related_name='laws', null=True, blank=True, to='op_scraper.Law'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='law',
            unique_together=set([('parl_id', 'legislative_period')]),
        ),
    ]
