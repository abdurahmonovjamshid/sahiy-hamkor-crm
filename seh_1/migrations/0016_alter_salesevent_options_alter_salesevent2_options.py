# Generated by Django 4.2.5 on 2024-01-02 07:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0015_remove_product_total_sold'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='salesevent',
            options={'verbose_name': 'Tayyor mahsulot', 'verbose_name_plural': 'Tayyor mahsulotlar'},
        ),
        migrations.AlterModelOptions(
            name='salesevent2',
            options={'verbose_name': 'Yaroqsiz mahsulot', 'verbose_name_plural': 'Yaroqsiz mahsulot'},
        ),
    ]
