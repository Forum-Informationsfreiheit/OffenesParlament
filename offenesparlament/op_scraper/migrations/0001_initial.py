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
            name='Administration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default=b'', unique=True, max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Comittee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=511)),
                ('parl_id', models.CharField(max_length=30)),
                ('source_link', models.URLField(default=b'', max_length=255)),
                ('nrbr', models.CharField(max_length=20)),
                ('description', models.TextField(default=b'', blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            bases=(models.Model, op_scraper.models.ParlIDMixIn),
        ),
        migrations.CreateModel(
            name='ComitteeAgendaTopic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField()),
                ('text', models.TextField()),
                ('comment', models.CharField(max_length=255, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ComitteeMeeting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField()),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='ComitteeMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_from', models.DateField()),
                ('date_to', models.DateField(null=True, blank=True)),
                ('comittee', models.ForeignKey(related_name='comittee_members', to='op_scraper.Comittee')),
            ],
        ),
        migrations.CreateModel(
            name='Debate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField()),
                ('title', models.CharField(max_length=255, null=True)),
                ('debate_type', models.CharField(max_length=255, null=True)),
                ('protocol_url', models.URLField(max_length=255, null=True)),
                ('detail_url', models.URLField(max_length=255, null=True, blank=True)),
                ('nr', models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DebateStatement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(null=True)),
                ('index', models.IntegerField(default=1)),
                ('doc_section', models.CharField(max_length=255)),
                ('text_type', models.CharField(max_length=12, null=True)),
                ('speaker_role', models.CharField(max_length=12, null=True)),
                ('page_start', models.IntegerField(null=True)),
                ('page_end', models.IntegerField(null=True)),
                ('full_text', models.TextField(null=True)),
                ('raw_text', models.TextField(null=True)),
                ('annotated_text', models.TextField(null=True)),
                ('speaker_name', models.CharField(max_length=255, null=True)),
                ('debugdump', models.TextField(null=True)),
                ('debate', models.ForeignKey(related_name='debate_statements', to='op_scraper.Debate', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1023)),
                ('pdf_link', models.URLField(max_length=255, null=True)),
                ('html_link', models.URLField(max_length=255, null=True)),
                ('stripped_html', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1023)),
                ('title_detail', models.CharField(max_length=1023)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Function',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1023)),
                ('short', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=255)),
                ('_title_urlsafe', models.CharField(default=b'', max_length=255)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Law',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1023)),
                ('status', models.TextField(null=True, blank=True)),
                ('source_link', models.URLField(default=b'', max_length=255)),
                ('parl_id', models.CharField(default=b'', max_length=30)),
                ('description', models.TextField(blank=True)),
                ('_slug', models.CharField(default=b'', max_length=255)),
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
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('administration', models.ForeignKey(blank=True, to='op_scraper.Administration', null=True)),
                ('function', models.ForeignKey(to='op_scraper.Function')),
                ('legislative_period', models.ForeignKey(blank=True, to='op_scraper.LegislativePeriod', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Opinion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('parl_id', models.CharField(default=b'', unique=True, max_length=120)),
                ('date', models.DateField(null=True)),
                ('description', models.TextField(blank=True)),
                ('source_link', models.URLField(default=b'', max_length=255)),
                ('category', models.ForeignKey(blank=True, to='op_scraper.Category', null=True)),
                ('documents', models.ManyToManyField(to='op_scraper.Document')),
                ('entity', models.ForeignKey(related_name='opinions', to='op_scraper.Entity')),
                ('keywords', models.ManyToManyField(to='op_scraper.Keyword')),
            ],
            options={
                'ordering': ['date'],
            },
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
                ('source_link', models.URLField(default=b'', max_length=255)),
                ('photo_link', models.URLField(default=b'', max_length=255)),
                ('photo_copyright', models.CharField(default=b'', max_length=255)),
                ('full_name', models.CharField(max_length=255)),
                ('reversed_name', models.CharField(max_length=255)),
                ('birthdate', models.DateField(null=True, blank=True)),
                ('birthplace', models.CharField(max_length=255, null=True, blank=True)),
                ('deathdate', models.DateField(null=True, blank=True)),
                ('deathplace', models.CharField(max_length=255, null=True, blank=True)),
                ('occupation', models.CharField(max_length=255, null=True, blank=True)),
                ('ts', models.DateTimeField(null=True)),
                ('_slug', models.CharField(default=b'', max_length=255)),
                ('latest_mandate', models.ForeignKey(related_name='latest_mandate', blank=True, to='op_scraper.Mandate', null=True)),
                ('mandates', models.ManyToManyField(to='op_scraper.Mandate')),
            ],
            bases=(models.Model, op_scraper.models.ParlIDMixIn),
        ),
        migrations.CreateModel(
            name='PetitionCreator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(max_length=255)),
                ('person', models.OneToOneField(related_name='petitions_created', null=True, to='op_scraper.Person')),
            ],
        ),
        migrations.CreateModel(
            name='PetitionSignature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(max_length=255)),
                ('postal_code', models.CharField(max_length=50)),
                ('location', models.CharField(max_length=255)),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Phase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1023)),
            ],
        ),
        migrations.CreateModel(
            name='PressRelease',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1023)),
                ('subtitle', models.CharField(max_length=1023)),
                ('full_text', models.TextField()),
                ('release_date', models.DateField()),
                ('source_link', models.URLField(default=b'', max_length=255)),
                ('parl_id', models.CharField(default=b'', unique=True, max_length=30)),
                ('topics', models.CharField(max_length=255)),
                ('format', models.CharField(max_length=255)),
                ('tags', models.CharField(max_length=255)),
            ],
            bases=(models.Model, op_scraper.models.ParlIDMixIn),
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=1023)),
            ],
        ),
        migrations.CreateModel(
            name='Statement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('speech_type', models.CharField(max_length=255)),
                ('protocol_url', models.URLField(default=b'', max_length=255)),
                ('index', models.IntegerField(default=1)),
                ('person', models.ForeignKey(related_name='statements', to='op_scraper.Person')),
            ],
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1023)),
                ('sortkey', models.CharField(max_length=6)),
                ('date', models.DateField()),
                ('protocol_url', models.URLField(default=b'', max_length=255)),
                ('source_link', models.URLField(default=b'', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SubscribedContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(unique=True, max_length=255)),
                ('latest_content_hash', models.CharField(max_length=16, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_unsub_slug', models.CharField(default=b'', max_length=255)),
                ('content', models.ForeignKey(to='op_scraper.SubscribedContent')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(unique=True, max_length=254)),
                ('_list_slug', models.CharField(default=b'', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Verification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('verified', models.BooleanField()),
                ('verification_hash', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Petition',
            fields=[
                ('law_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='op_scraper.Law')),
                ('signable', models.BooleanField()),
                ('signing_url', models.URLField(default=b'', max_length=255)),
                ('signature_count', models.IntegerField(default=0)),
                ('reference', models.OneToOneField(related_name='redistribution', null=True, blank=True, to='op_scraper.Petition')),
            ],
            bases=('op_scraper.law',),
        ),
        migrations.AddField(
            model_name='user',
            name='verification',
            field=models.OneToOneField(null=True, blank=True, to='op_scraper.Verification'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='user',
            field=models.ForeignKey(to='op_scraper.User'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='verification',
            field=models.OneToOneField(null=True, blank=True, to='op_scraper.Verification'),
        ),
        migrations.AddField(
            model_name='subscribedcontent',
            name='users',
            field=models.ManyToManyField(to='op_scraper.User', through='op_scraper.Subscription'),
        ),
        migrations.AddField(
            model_name='step',
            name='law',
            field=models.ForeignKey(related_name='steps', blank=True, to='op_scraper.Law', null=True),
        ),
        migrations.AddField(
            model_name='step',
            name='opinion',
            field=models.ForeignKey(related_name='steps', blank=True, to='op_scraper.Opinion', null=True),
        ),
        migrations.AddField(
            model_name='step',
            name='phase',
            field=models.ForeignKey(to='op_scraper.Phase'),
        ),
        migrations.AddField(
            model_name='statement',
            name='step',
            field=models.ForeignKey(related_name='statements', to='op_scraper.Step'),
        ),
        migrations.AddField(
            model_name='opinion',
            name='prelaw',
            field=models.ForeignKey(related_name='opinions', to='op_scraper.Law'),
        ),
        migrations.AddField(
            model_name='mandate',
            name='party',
            field=models.ForeignKey(blank=True, to='op_scraper.Party', null=True),
        ),
        migrations.AddField(
            model_name='mandate',
            name='state',
            field=models.ForeignKey(blank=True, to='op_scraper.State', null=True),
        ),
        migrations.AddField(
            model_name='law',
            name='category',
            field=models.ForeignKey(blank=True, to='op_scraper.Category', null=True),
        ),
        migrations.AddField(
            model_name='law',
            name='documents',
            field=models.ManyToManyField(related_name='laws', to='op_scraper.Document'),
        ),
        migrations.AddField(
            model_name='law',
            name='keywords',
            field=models.ManyToManyField(related_name='laws', to='op_scraper.Keyword'),
        ),
        migrations.AddField(
            model_name='law',
            name='legislative_period',
            field=models.ForeignKey(blank=True, to='op_scraper.LegislativePeriod', null=True),
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
            name='function',
            unique_together=set([('title', 'short')]),
        ),
        migrations.AlterUniqueTogether(
            name='entity',
            unique_together=set([('title', 'title_detail')]),
        ),
        migrations.AddField(
            model_name='debatestatement',
            name='person',
            field=models.ForeignKey(related_name='debate_statements', to='op_scraper.Person', null=True),
        ),
        migrations.AddField(
            model_name='debate',
            name='llp',
            field=models.ForeignKey(blank=True, to='op_scraper.LegislativePeriod', null=True),
        ),
        migrations.AddField(
            model_name='comitteemembership',
            name='function',
            field=models.ForeignKey(related_name='comittee_function', to='op_scraper.Function'),
        ),
        migrations.AddField(
            model_name='comitteemembership',
            name='person',
            field=models.ForeignKey(related_name='comittee_memberships', to='op_scraper.Person'),
        ),
        migrations.AddField(
            model_name='comitteemeeting',
            name='agenda',
            field=models.OneToOneField(related_name='comittee_meeting', null=True, to='op_scraper.Document'),
        ),
        migrations.AddField(
            model_name='comitteemeeting',
            name='comittee',
            field=models.ForeignKey(related_name='comittee_meetings', to='op_scraper.Comittee'),
        ),
        migrations.AddField(
            model_name='comitteeagendatopic',
            name='law',
            field=models.ForeignKey(related_name='agenda_topics', to='op_scraper.Law', null=True),
        ),
        migrations.AddField(
            model_name='comitteeagendatopic',
            name='meeting',
            field=models.ForeignKey(related_name='agenda_topics', to='op_scraper.ComitteeMeeting'),
        ),
        migrations.AddField(
            model_name='comittee',
            name='laws',
            field=models.ManyToManyField(related_name='comittees', to='op_scraper.Law', blank=True),
        ),
        migrations.AddField(
            model_name='comittee',
            name='legislative_period',
            field=models.ForeignKey(blank=True, to='op_scraper.LegislativePeriod', null=True),
        ),
        migrations.AddField(
            model_name='comittee',
            name='parent_comittee',
            field=models.ForeignKey(related_name='sub_comittees', blank=True, to='op_scraper.Comittee', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('user', 'content')]),
        ),
        migrations.AddField(
            model_name='petitionsignature',
            name='petition',
            field=models.ForeignKey(related_name='petition_signatures', to='op_scraper.Petition'),
        ),
        migrations.AddField(
            model_name='petitioncreator',
            name='created_petitions',
            field=models.ManyToManyField(related_name='creators', to='op_scraper.Petition'),
        ),
        migrations.AlterUniqueTogether(
            name='law',
            unique_together=set([('parl_id', 'legislative_period')]),
        ),
        migrations.AlterUniqueTogether(
            name='comitteemeeting',
            unique_together=set([('number', 'date', 'comittee')]),
        ),
        migrations.AlterUniqueTogether(
            name='comittee',
            unique_together=set([('parl_id', 'legislative_period', 'active')]),
        ),
    ]
