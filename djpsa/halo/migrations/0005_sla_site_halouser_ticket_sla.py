# Generated by Django 4.2.11 on 2024-09-13 13:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('halo', '0004_alter_agent_options_alter_client_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SLA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('hours_are_local_time', models.BooleanField(default=False)),
                ('hours_are_techs_local_time', models.BooleanField(default=False)),
                ('response_reset', models.BooleanField(default=False)),
                ('response_reset_approval', models.BooleanField(default=False)),
                ('track_sla_fix_by_time', models.BooleanField(default=True)),
                ('track_sla_response_time', models.BooleanField(default=True)),
                ('workday_id', models.IntegerField(blank=True, null=True)),
                ('auto_release_limit', models.IntegerField(blank=True, null=True)),
                ('auto_release_option', models.BooleanField(default=False)),
                ('status_after_first_warning', models.IntegerField(blank=True, null=True)),
                ('status_after_second_warning', models.IntegerField(blank=True, null=True)),
                ('status_after_auto_release', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('colour', models.CharField(blank=True, max_length=50, null=True)),
                ('active', models.BooleanField(default=True)),
                ('phone_number', models.CharField(blank=True, max_length=250, null=True)),
                ('use', models.CharField(max_length=255)),
                ('delivery_address', models.BooleanField(max_length=1000)),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.client')),
                ('sla', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.sla')),
            ],
        ),
        migrations.CreateModel(
            name='HaloUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('first_name', models.CharField(max_length=255)),
                ('initials', models.CharField(max_length=10)),
                ('surname', models.CharField(max_length=255)),
                ('email', models.EmailField(blank=True, max_length=250, null=True)),
                ('colour', models.CharField(blank=True, max_length=50, null=True)),
                ('active', models.BooleanField(default=True)),
                ('login', models.CharField(max_length=255)),
                ('use', models.CharField(max_length=255)),
                ('never_send_emails', models.BooleanField(default=False)),
                ('phone_number', models.CharField(blank=True, max_length=250, null=True)),
                ('mobile_number', models.CharField(blank=True, max_length=250, null=True)),
                ('mobile_number_2', models.CharField(blank=True, max_length=250, null=True)),
                ('home_number', models.CharField(blank=True, max_length=250, null=True)),
                ('tel_pref', models.IntegerField(blank=True, null=True)),
                ('is_service_account', models.BooleanField(default=False)),
                ('is_important_contact', models.BooleanField(default=False)),
                ('is_important_contact_2', models.BooleanField(default=False)),
                ('agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.agent')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.client')),
                ('site', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.site')),
            ],
        ),
        migrations.AddField(
            model_name='ticket',
            name='sla',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.sla'),
        ),
    ]