# Generated by Django 4.2.5 on 2023-09-12 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0006_alter_productproduction_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='total_cut',
            field=models.IntegerField(default=0, verbose_name='Kesilganlar soni'),
        ),
        migrations.AlterField(
            model_name='product',
            name='total_sold',
            field=models.IntegerField(default=0, verbose_name='sotilganlar soni'),
        ),
    ]
