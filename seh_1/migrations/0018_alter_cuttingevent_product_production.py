# Generated by Django 4.2.5 on 2023-09-13 12:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0017_alter_cuttingevent_product_production'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuttingevent',
            name='product_production',
            field=models.ForeignKey(limit_choices_to={'total_cut': 0}, on_delete=django.db.models.deletion.CASCADE, to='seh_1.productproduction'),
        ),
    ]
