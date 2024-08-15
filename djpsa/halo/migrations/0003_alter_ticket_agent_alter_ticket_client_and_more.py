# Generated by Django 4.2.11 on 2024-08-15 14:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('halo', '0002_rename_isdisabled_agent_is_disabled_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='agent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.agent'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.client'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='priority',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.priority'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='summary',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
