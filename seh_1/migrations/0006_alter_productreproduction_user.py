# Generated by Django 4.2.5 on 2023-10-07 08:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('seh_1', '0005_sales_user_alter_sales_date_alter_sales_seller'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productreproduction',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Xodim'),
        ),
    ]
