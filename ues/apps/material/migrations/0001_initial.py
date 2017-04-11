# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Classify',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('codename', models.CharField(default=b'others', max_length=50, verbose_name='\u82f1\u6587\u540d\u79f0')),
                ('chinesename', models.CharField(default=b'\xe5\x85\xb6\xe4\xbb\x96', max_length=50, verbose_name='\u4e2d\u6587\u540d\u79f0')),
                ('children', models.ManyToManyField(default=None, to='material.Classify', verbose_name='\u5b50\u7c7b', blank=True)),
            ],
            options={
                'db_table': 'ues_classify',
                'verbose_name': '\u9898\u76ee\u5206\u7c7b',
            },
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('repo', models.CharField(max_length=20, verbose_name='\u9898\u76ee\u7c7b\u578b')),
                ('label', models.CharField(max_length=45, verbose_name='\u9898\u76ee\u7f16\u53f7')),
                ('rating', models.FloatField(default=1, verbose_name='\u9898\u76ee\u96be\u5ea6')),
                ('classify', models.ManyToManyField(default=None, to='material.Classify', verbose_name='\u9898\u76ee\u5206\u7c7b', blank=True)),
            ],
            options={
                'db_table': 'ues_material',
                'verbose_name': '\u9898\u76ee\u5c5e\u6027',
            },
        ),
        migrations.AlterUniqueTogether(
            name='material',
            unique_together=set([('repo', 'label')]),
        ),
        migrations.AlterIndexTogether(
            name='material',
            index_together=set([('repo', 'label')]),
        ),
        migrations.AlterUniqueTogether(
            name='classify',
            unique_together=set([('codename',)]),
        ),
    ]
