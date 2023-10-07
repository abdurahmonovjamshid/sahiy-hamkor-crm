# Generated by Django 4.2.5 on 2023-10-07 08:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('seh_1', '0004_alter_cuttingevent_product_production_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Xodim'),
        ),
        migrations.AlterField(
            model_name='sales',
            name='date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Sotilgan sana'),
        ),
        migrations.AlterField(
            model_name='sales',
            name='seller',
            field=models.CharField(default=' ', max_length=250, verbose_name='Sotuvchi'),
            preserve_default=False,
        ),
    ]