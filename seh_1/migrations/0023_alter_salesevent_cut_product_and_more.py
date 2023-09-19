# Generated by Django 4.2.5 on 2023-09-19 14:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0022_alter_salesevent_cut_product_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salesevent',
            name='cut_product',
            field=models.ForeignKey(limit_choices_to={'quantity_cut__gt': 0}, on_delete=django.db.models.deletion.CASCADE, to='seh_1.cuttingevent'),
        ),
        migrations.AlterField(
            model_name='salesevent2',
            name='non_cut_product',
            field=models.ForeignKey(limit_choices_to={'quantity__gt': 0}, on_delete=django.db.models.deletion.CASCADE, to='seh_1.productproduction'),
        ),
    ]
