# Generated by Django 4.2.11 on 2024-08-14 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('isdisabled', models.BooleanField(default=False)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('initials', models.CharField(blank=True, max_length=10, null=True)),
                ('firstname', models.CharField(blank=True, max_length=255, null=True)),
                ('surname', models.CharField(blank=True, max_length=255, null=True)),
                ('colour', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inactive', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Priority',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('ishidden', models.BooleanField(default=False)),
                ('colour', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('colour', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('summary', models.CharField(max_length=255)),
                ('details', models.TextField(blank=True, max_length=8000, null=True)),
                ('lastactiondate', models.DateField(blank=True, null=True)),
                ('last_update', models.DateTimeField(blank=True, null=True)),
                ('targetdate', models.DateField(blank=True, null=True)),
                ('targettime', models.TimeField(blank=True, null=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='halo.agent')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='halo.client')),
                ('priority', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='halo.priority')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='halo.status')),
            ],
        ),
    ]
