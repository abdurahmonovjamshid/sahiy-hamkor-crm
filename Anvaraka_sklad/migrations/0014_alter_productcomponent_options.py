# Generated by Django 4.2.5 on 2023-11-05 10:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Anvaraka_sklad', '0013_sales_quantity_in_measurement_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productcomponent',
            options={'ordering': ('-quantity',)},
        ),
    ]