# Generated by Django 4.2.5 on 2024-01-02 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Azamat_seh', '0010_salesevent_profit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productproduction',
            name='quantity',
            field=models.PositiveIntegerField(verbose_name='Ishlab chiqarilganlar soni'),
        ),
    ]
