# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('op_scraper', '0009_auto_20170703_2201'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentedcontent',
            name='approved_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='commentedcontent',
            name='created_by_link',
            field=models.URLField(default='', max_length=250, verbose_name=b'Website des Autors'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='commentedcontent',
            name='body',
            field=models.TextField(help_text=b'\xc3\x9cberschriften und Formatierung im Markdown-Format, Links auf OffenesParlament.at werden verlinkt', verbose_name=b'Text'),
        ),
        migrations.AlterField(
            model_name='commentedcontent',
            name='created_by_name',
            field=models.CharField(max_length=120, verbose_name=b'Name des Autors oder der Organisation'),
        ),
        migrations.AlterField(
            model_name='commentedcontent',
            name='image',
            field=models.ImageField(help_text=b'Wird auf 100pxx100px verkleinert und in einem Kreis dargestellt', upload_to=b'', null=True, verbose_name=b'Autorenbild'),
        ),
        migrations.AlterField(
            model_name='commentedcontent',
            name='title',
            field=models.CharField(max_length=240, verbose_name=b'Titel'),
        ),
    ]
