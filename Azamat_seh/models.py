from openpyxl import Workbook
from mptt.models import MPTTModel
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Q
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.auth import get_user_model
User = get_user_model()


class Component(MPTTModel):
    MEASUREMENT_CHOICES = [
        ('kg', 'Kilogram'),
        ('l', 'Litr'),
        ('pc', 'Dona'),
    ]

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, verbose_name="Bo'limlar",
                               limit_choices_to={'parent__isnull': True},
                               related_name='children', null=True, blank=True, )

    title = models.CharField(max_length=100, verbose_name='Nomi')
    price = models.FloatField(verbose_name='Narx')
    measurement = models.CharField(
        max_length=2, choices=MEASUREMENT_CHOICES, verbose_name="O'lchov birligi")

    total = models.FloatField(default=0, verbose_name='Umumiy')
    notification_limit = models.IntegerField(
        default=500, verbose_name="Ogohlantirish")

    class Meta:
        verbose_name = 'Komponent '
        verbose_name_plural = 'Komponentlar'

    class MPTTMeta:
        order_insertion_by = ['title']

    def __str__(self):
        return self.title + f' ({self.get_measurement_display()})'

    @property
    def highlight(self):
        children = self.children.all()
        for child in children:
            if child.total < child.notification_limit:
                return True
        return False


class Product(MPTTModel):
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, verbose_name="Bo'limlar",
                               limit_choices_to={'parent__isnull': True},
                               related_name='children', null=True, blank=True, )
    name = models.CharField(max_length=100, verbose_name='Nomi')
    price = models.FloatField(verbose_name='Sotuv narxi')

    total_new = models.IntegerField(
        default=0, verbose_name="Ishlab chiqarilganlar soni")
    total_sold = models.IntegerField(
        default=0, verbose_name="Sotilganlar soni")
    total_sold_price = models.FloatField(
        verbose_name='Umumiy sotilgan narxi', default=0)

    class Meta:
        verbose_name = 'Tovar '
        verbose_name_plural = 'Tovarlar'

    def __str__(self):
        return self.name


class ProductComponent(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='product')
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE, verbose_name="Komponent", limit_choices_to={'parent__isnull': False})
    quantity = models.FloatField(verbose_name="miqdor")

    class Meta:
        unique_together = ('product', 'component')

    def __str__(self):
        return f'({self.quantity} {self.component.get_measurement_display()})'


class ProductProduction(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, verbose_name='xodim', null=True, blank=True, related_name='production')

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='Produkt', limit_choices_to={'parent__isnull': False})
    quantity = models.PositiveIntegerField(verbose_name="Kesilmaganlar soni")

    date = models.DateTimeField(
        auto_now_add=True, verbose_name='Ishlab chiqarilish vaqti')

    class Meta:
        verbose_name = 'Tovar '
        verbose_name_plural = 'Tovarlar Ishlab Chiqarish'
        ordering = ['-date']

    def __str__(self):
        return f'{self.quantity} dona {self.product}'


class Warehouse(models.Model):
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE, verbose_name='Komponent', limit_choices_to={'parent__isnull': False})
    quantity = models.IntegerField(verbose_name="Miqdor")
    price = models.FloatField(default=0, verbose_name='Narxi')
    date = models.DateTimeField(
        auto_now_add=True, verbose_name='Keltirilgan sana')

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='xodim', related_name='income')

    class Meta:
        verbose_name = 'Keltirilgan Komponentlar '
        verbose_name_plural = 'Ombor'

    def save(self, *args, **kwargs):
        self.price = self.component.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} {self.component.get_measurement_display()} - {self.component.title}"


class Sales(models.Model):
    buyer = models.CharField(max_length=250, verbose_name='Sotuvchi')
    seller = models.CharField(max_length=250, verbose_name='Haridor')

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Xodim', related_name='sale')
    date = models.DateTimeField(
        auto_now_add=True, verbose_name='Sotilgan sana')

    class Meta:
        verbose_name = 'Sotuv '
        verbose_name_plural = "Sotuv Bo'limi "

    def __str__(self):
        return self.buyer


class SalesEvent(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=False, blank=False, limit_choices_to={'total_new__gt': 0, })
    quantity_sold = models.PositiveIntegerField(
        verbose_name="Sotilganlar soni")
    sales = models.ForeignKey(
        Sales, on_delete=models.CASCADE, related_name='selling_cut')
    single_sold_price = models.FloatField(
        verbose_name='sotilgan narxi')

    total_sold_price = models.FloatField(
        verbose_name='Umumiy sotilgan narxi')

    def clean(self):
        super().clean()
        if self.product:
            if self.quantity_sold > self.product.total_new:
                raise ValidationError(
                    "sotilgan qiymat mavjud qiymatdan oshib ketdi")

    def save(self, *args, **kwargs):
        self.single_sold_price = self.product.price
        self.total_sold_price = self.single_sold_price * self.quantity_sold
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Mahsulot'
        verbose_name_plural = 'Mahsulotlar'
        unique_together = ['product', 'sales']

    def __str__(self):
        return str(self.quantity_sold)+' ta '+self.product.name
