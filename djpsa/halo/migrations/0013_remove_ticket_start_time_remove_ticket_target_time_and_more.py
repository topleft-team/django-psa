# Generated by Django 4.2.11 on 2024-10-15 13:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('halo', '0012_alter_client_main_site'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='start_time',
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='target_time',
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_arrival_date', models.DateTimeField(blank=True, null=True)),
                ('action_completion_date', models.DateTimeField(blank=True, null=True)),
                ('action_date_created', models.DateTimeField(blank=True, null=True)),
                ('time_taken', models.FloatField(blank=True, null=True)),
                ('time_taken_adjusted', models.FloatField(blank=True, null=True)),
                ('time_taken_days', models.FloatField(blank=True, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('action_charge_amount', models.FloatField(blank=True, null=True)),
                ('action_charge_hours', models.FloatField(blank=True, null=True)),
                ('action_non_charge_amount', models.FloatField(blank=True, null=True)),
                ('action_non_charge_hours', models.FloatField(blank=True, null=True)),
                ('act_is_billable', models.BooleanField(default=False)),
                ('attachment_count', models.IntegerField(blank=True, null=True)),
                ('charge_rate', models.IntegerField(blank=True, null=True)),
                ('hidden_from_user', models.BooleanField(default=False)),
                ('important', models.BooleanField(default=False)),
                ('agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.agent')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.ticket')),
                ('ticket', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.ticket')),
            ],
            options={
                'verbose_name_plural': 'Actions',
            },
        ),
        migrations.CreateModel(
            name='ActionTracker',
            fields=[
            ],
            options={
                'db_table': 'halo_action',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('halo.action',),
        ),
    ]
