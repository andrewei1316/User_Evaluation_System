# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackgroundKnowledge',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('repo', models.CharField(max_length=20, verbose_name='\u9898\u76ee\u7c7b\u578b')),
                ('label', models.CharField(max_length=45, verbose_name='\u9898\u76ee\u7f16\u53f7')),
                ('classify', models.ManyToManyField(default=None, to='material.Classify', verbose_name='\u9898\u76ee\u5206\u7c7b', blank=True)),
            ],
            options={
                'db_table': 'ues_background_knowledge',
                'verbose_name': '\u80cc\u666f\u77e5\u8bc6',
            },
        ),
        migrations.AlterUniqueTogether(
            name='backgroundknowledge',
            unique_together=set([('repo', 'label')]),
        ),
        migrations.AlterIndexTogether(
            name='backgroundknowledge',
            index_together=set([('repo', 'label')]),
        ),
    ]
