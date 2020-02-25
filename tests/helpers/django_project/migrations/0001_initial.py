# -*- coding: utf-8 -*-
# Generated by Django 2.2.4 on 2019-08-24 19:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
                ('cost', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cost', models.IntegerField()),
                ('period', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='django_project.Category')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='django_project.Profile')),
            ],
            options={
                'unique_together': {('category', 'profile')},
            },
        ),
    ]
