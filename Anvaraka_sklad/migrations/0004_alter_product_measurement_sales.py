# Generated by Django 4.2.6 on 2023-11-02 14:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Anvaraka_sklad', '0003_alter_product_measurement_warehouse'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='measurement',
            field=models.CharField(choices=[('kg', 'Kilogram'), ('l', 'Litr'), ('m', 'Metr'), ('ta', 'Dona')], max_length=2, verbose_name="O'lchov birligi"),
        ),
        migrations.CreateModel(
            name='Sales',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(verbose_name='Miqdor')),
                ('price', models.FloatField(default=0, verbose_name='Narxi')),
                ('total_price', models.FloatField(default=0, verbose_name='Umumiy narxi')),
                ('sold_time', models.DateTimeField(auto_now_add=True, verbose_name='Sotilgan sana')),
                ('component', models.ForeignKey(limit_choices_to={'parent__isnull': False}, on_delete=django.db.models.deletion.CASCADE, to='Anvaraka_sklad.product', verbose_name='Sotilgan mahsulot ')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='xodim')),
            ],
            options={
                'verbose_name': 'Sotilgan Mahsulot ',
                'verbose_name_plural': 'Sotuv',
            },
        ),
    ]