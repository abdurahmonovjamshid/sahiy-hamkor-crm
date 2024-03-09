from django.db.models import Sum
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from mptt.models import MPTTModel
from openpyxl import Workbook


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


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nomi')
    invalid_price = models.FloatField(verbose_name='Yaroqsiz tovar narxi')
    price = models.FloatField(verbose_name='Sotuv narxi')

    total_new = models.IntegerField(
        default=0, verbose_name="Kesilmaganlar soni")
    total_cut = models.IntegerField(
        default=0, verbose_name="Kesilganlar soni")

    class Meta:
        verbose_name = 'Produkt '
        verbose_name_plural = 'Produktlar'

    def __str__(self):
        return self.name

    def calculate_product_price(self):
        product_price = 0
        for productcomponent in self.productcomponent_set.all():
            product_price += productcomponent.quantity*productcomponent.component.price
        return product_price


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
        User, on_delete=models.SET_NULL, verbose_name='xodim', null=True, blank=True)

    series = models.CharField(max_length=50, verbose_name="Seriya")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='Produkt')
    quantity = models.PositiveIntegerField(verbose_name="Kesilmaganlar soni")

    date = models.DateTimeField(
        auto_now_add=True, verbose_name='Ishlab chiqarilish vaqti')

    class Meta:
        verbose_name = 'Tovar '
        verbose_name_plural = 'Ishlab Chiqarilgan Tovarlar'
        ordering = ['-id']

    def __str__(self):
        return f'{self.series}-{self.product} ({self.quantity} dona'


class Warehouse(models.Model):
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE, verbose_name='Komponent', limit_choices_to={'parent__isnull': False})
    quantity = models.IntegerField(verbose_name="Miqdor")
    price = models.FloatField(default=0, verbose_name='Narxi')
    arrival_time = models.DateTimeField(
        auto_now_add=True, verbose_name='Keltirilgan sana')

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='xodim')

    class Meta:
        verbose_name = 'Keltirilgan Komponentlar '
        verbose_name_plural = 'Ombor'

    def save(self, *args, **kwargs):
        self.price = self.component.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} {self.component.get_measurement_display()} - {self.component.title}"


class ProductReProduction(models.Model):
    series = models.CharField(max_length=50, verbose_name="Seriya")
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Xodim')
    date = models.DateTimeField(
        auto_now_add=True, verbose_name='Kesilgan vaqti')
    
    @property
    def total_quantity_cut(obj):
        return obj.cutting.aggregate(
            total=Sum('quantity_cut'))['total']
    
    @property
    def get_cutting_events(obj):
        cutting_events = obj.cutting.all()
        return ", ".join(str(str(cutting_event.quantity_cut) + ' ta ' + cutting_event.product.name) for cutting_event in cutting_events)

    def __str__(self):
        return f'{self.series} - {self.get_cutting_events}'

    class Meta:
        verbose_name = 'Kesilgan tovarlar '
        verbose_name_plural = 'Kesish Bo\'limi'


class CuttingEvent(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=False, blank=False, limit_choices_to={'total_new__gt': 0}, verbose_name='Tovar')
    quantity_cut = models.PositiveIntegerField(verbose_name="Kesilganlar soni")
    product_reproduction = models.ForeignKey(
        ProductReProduction, on_delete=models.CASCADE, related_name='cutting')

    def clean(self):
        super().clean()
        if self.product_id:
            if self.quantity_cut > self.product.total_new:
                raise ValidationError(
                    "Kesilgan qiymat ishlab chiqarilgan qiymatdan oshib ketdi")
        else:
            raise ValidationError(
                "xatolik")

    def __str__(self):
        return f"{self.quantity_cut} cut from {self.product_reproduction.series}-{self.product.name}"

    class Meta:
        verbose_name = 'Kesish'
        verbose_name_plural = 'Kesish'
        unique_together = ['product', 'product_reproduction']


class Sales(models.Model):
    series = models.CharField(max_length=50, verbose_name="Seriya")
    buyer = models.CharField(max_length=250, verbose_name='Sotuvchi')
    seller = models.CharField(max_length=250, verbose_name='Haridor')
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Xodim')
    date = models.DateTimeField(
        auto_now_add=True, verbose_name='Sotilgan sana')

    def calculate_total_price(self):
        sales_events = self.selling_cut.all()
        total_price = sum(event.total_sold_price for event in sales_events)
        return total_price

    def save(self, *args, **kwargs):
        self.buyer = self.buyer.title()
        self.seller = self.seller.title()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Sotuv '
        verbose_name_plural = "Sotuv Bo'limi "

    def __str__(self):
        total_price = self.calculate_total_price()
        return f"{self.buyer} - {self.seller} - {total_price}$"


class SalesEvent(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=False, blank=False, limit_choices_to={'total_cut__gt': 0})
    quantity_sold = models.PositiveIntegerField(
        verbose_name="Sotilganlar soni")
    sales = models.ForeignKey(
        Sales, on_delete=models.CASCADE, related_name='selling_cut')
    single_sold_price = models.FloatField(
        verbose_name='sotilgan narxi')

    total_sold_price = models.FloatField(
        verbose_name='Umumiy sotilgan narxi')
    profit = models.FloatField(default=0, verbose_name='Foyda')

    def clean(self):
        super().clean()
        if self.product:
            if self.quantity_sold > self.product.total_cut:
                raise ValidationError(
                    "sotilgan qiymat kesilgan qiymatdan oshib ketdi")

    def save(self, *args, **kwargs):
        self.single_sold_price = self.product.price
        self.total_sold_price = self.single_sold_price * self.quantity_sold

        self.profit = self.total_sold_price - \
            (self.product.calculate_product_price() * self.quantity_sold)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Tayyor mahsulot'
        verbose_name_plural = 'Tayyor mahsulotlar'
        unique_together = ['product', 'sales']

    def __str__(self):
        return str(self.quantity_sold)+' ta '+self.product.name


class SalesEvent2(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=False, blank=False, limit_choices_to={'total_new__gt': 0})
    quantity_sold = models.PositiveIntegerField(
        verbose_name="Sotilganlar soni")
    sales = models.ForeignKey(
        Sales, on_delete=models.CASCADE, related_name='selling')

    single_sold_price = models.FloatField(
        verbose_name='sotilgan narxi')

    total_sold_price = models.FloatField(
        verbose_name='Umumiy sotilgan narxi')

    profit = models.FloatField(default=0, verbose_name='Foyda')

    def clean(self):
        super().clean()
        if self.product:
            if self.quantity_sold > self.product.total_new:
                raise ValidationError(
                    "sotilgan qiymat kesilmagan qiymatdan oshib ketdi")

    def save(self, *args, **kwargs):
        self.single_sold_price = self.product.invalid_price
        self.total_sold_price = self.single_sold_price * self.quantity_sold

        self.profit = self.total_sold_price - \
            (self.product.calculate_product_price() * self.quantity_sold)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Yaroqsiz mahsulot'
        verbose_name_plural = 'Yaroqsiz mahsulot'
        unique_together = ['product', 'sales']

    def __str__(self):
        return str(self.quantity_sold)+' ta '+self.product.name
