# Generated by Django 4.2.5 on 2023-11-17 15:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Azamat_seh', '0003_alter_product_options_alter_salesevent_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productproduction',
            options={'ordering': ['-production_date'], 'verbose_name': 'Tovar ', 'verbose_name_plural': 'Tovarlar Ishlab Chiqarish'},
        ),
    ]