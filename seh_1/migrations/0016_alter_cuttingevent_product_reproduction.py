# Generated by Django 4.2.5 on 2023-09-12 16:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0015_alter_cuttingevent_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuttingevent',
            name='product_reproduction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cutting', to='seh_1.productreproduction'),
        ),
    ]