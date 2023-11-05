# Generated by Django 4.2.5 on 2023-11-05 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Anvaraka_sklad', '0006_product_currency_sales_buyer_alter_sales_quantity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='warehouse',
            name='quantity_in_measurement',
            field=models.FloatField(default=1, verbose_name='Miqdor'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='quantity',
            field=models.IntegerField(verbose_name='Dona'),
        ),
    ]