# Generated by Django 4.2.5 on 2023-11-09 10:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0003_alter_productproduction_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productproduction',
            options={'verbose_name': 'Tovar ', 'verbose_name_plural': 'Ishlab Chiqarilgan Tovarlar'},
        ),
        migrations.RemoveField(
            model_name='cuttingevent',
            name='quantity_sold',
        ),
    ]
