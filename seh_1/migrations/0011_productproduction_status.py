# Generated by Django 4.2.5 on 2023-09-09 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0010_alter_productproduction_series'),
    ]

    operations = [
        migrations.AddField(
            model_name='productproduction',
            name='status',
            field=models.CharField(choices=[('kesilgan', 'Kesilgan'), ('kesilmagan', 'Kesilmagan')], default='kesilmagan', max_length=20),
        ),
    ]
