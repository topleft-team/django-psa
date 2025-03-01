# Generated by Django 4.2.11 on 2024-12-13 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('halo', '0016_alter_appointment_site_alter_client_main_site_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('ticket_count', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'Teams',
            },
        ),
        migrations.CreateModel(
            name='TeamTracker',
            fields=[
            ],
            options={
                'db_table': 'halo_team',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('halo.team',),
        ),
    ]
