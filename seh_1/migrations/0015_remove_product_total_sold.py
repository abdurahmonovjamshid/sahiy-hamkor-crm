# Generated by Django 4.2.5 on 2024-01-02 05:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0014_salesevent2_profit_alter_salesevent_profit'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='total_sold',
        ),
    ]