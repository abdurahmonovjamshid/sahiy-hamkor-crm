# Generated by Django 4.2.5 on 2023-11-05 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Anvaraka_sklad', '0009_alter_productcomponent_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productcomponent',
            name='quantity',
            field=models.IntegerField(verbose_name='Dona'),
        ),
    ]