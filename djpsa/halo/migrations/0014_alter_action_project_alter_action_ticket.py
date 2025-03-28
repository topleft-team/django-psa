# Generated by Django 4.2.11 on 2024-10-18 11:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('halo', '0013_remove_ticket_start_time_remove_ticket_target_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='project_actions', to='halo.ticket'),
        ),
        migrations.AlterField(
            model_name='action',
            name='ticket',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ticket_actions', to='halo.ticket'),
        ),
    ]
