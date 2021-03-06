# Generated by Django 3.0.3 on 2020-03-01 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('title', models.CharField(default='DEFAULT TITLE', max_length=50)),
                ('description', models.CharField(default='DEFAULT DESCRIPTION', max_length=500)),
                ('coordinates', models.CharField(default='()', max_length=32)),
                ('n_to', models.IntegerField(blank=True, null=True)),
                ('s_to', models.IntegerField(blank=True, null=True)),
                ('e_to', models.IntegerField(blank=True, null=True)),
                ('w_to', models.IntegerField(blank=True, null=True)),
                ('elevation', models.IntegerField(default=0)),
                ('terrain', models.CharField(default='NORMAL', max_length=32)),
            ],
        ),
    ]
