# Generated by Django 4.2.5 on 2023-11-08 14:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Anvaraka_sklad', '0003_alter_productcomponent_quantity_in_measurement_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productcomponent',
            name='box',
        ),
        migrations.RemoveField(
            model_name='sales',
            name='box',
        ),
        migrations.RemoveField(
            model_name='warehouse',
            name='box',
        ),
    ]
