# Generated by Django 4.2.5 on 2024-03-09 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0017_product_invalid_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sales',
            name='buyer',
            field=models.CharField(max_length=250, verbose_name='Sotuvchi'),
        ),
        migrations.AlterField(
            model_name='sales',
            name='seller',
            field=models.CharField(max_length=250, verbose_name='Haridor'),
        ),
    ]
