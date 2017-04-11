# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Squads',
            fields=[
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(default=None, blank=True)),
                ('create_user', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'ues_squads',
                'verbose_name': '\u8bad\u7ec3\u5c0f\u7ec4',
            },
        ),
        migrations.CreateModel(
            name='SquadsUser',
            fields=[
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('user', models.CharField(max_length=50)),
                ('name', models.CharField(default=None, max_length=50, blank=True)),
                ('nickname', models.CharField(default=None, max_length=50, blank=True)),
                ('squads', models.ForeignKey(to='squads.Squads', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False)),
            ],
            options={
                'db_table': 'ues_squads_user',
                'verbose_name': '\u5c0f\u7ec4\u6210\u5458',
            },
        ),
        migrations.AlterUniqueTogether(
            name='squads',
            unique_together=set([('id',)]),
        ),
        migrations.AlterIndexTogether(
            name='squads',
            index_together=set([('create_user', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='squadsuser',
            unique_together=set([('user', 'squads')]),
        ),
        migrations.AlterIndexTogether(
            name='squadsuser',
            index_together=set([('user', 'squads')]),
        ),
    ]
