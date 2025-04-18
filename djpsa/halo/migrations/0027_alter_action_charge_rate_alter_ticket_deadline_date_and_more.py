# Generated by Django 4.2.17 on 2025-03-20 14:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('halo', '0026_merge_20250314_1651'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='charge_rate',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.chargerate'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='deadline_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Deadline'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='estimate',
            field=models.FloatField(blank=True, help_text='Effort in hours', null=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='fix_by_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fix by'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='itil_request_type',
            field=models.IntegerField(choices=[(1, 'Incident'), (2, 'Change Request'), (3, 'Service Request'), (4, 'Problem'), (20, 'Request For Quote'), (21, 'Advice Other'), (22, 'Projects'), (23, 'Tasks')], default=1, verbose_name='ITIL request type'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='halo.halouser', verbose_name='Contact'),
        ),
    ]
