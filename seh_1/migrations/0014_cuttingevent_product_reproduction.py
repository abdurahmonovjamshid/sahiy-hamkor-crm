# Generated by Django 4.2.5 on 2023-09-12 16:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seh_1', '0013_productreproduction_cuttingevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuttingevent',
            name='product_reproduction',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='seh_1.productreproduction'),
            preserve_default=False,
        ),
    ]