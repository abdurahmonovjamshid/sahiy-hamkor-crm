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
    price = models.FloatField(verbose_name='Sotuv narxi')

    total_new = models.IntegerField(
        default=0, verbose_name="Kesilmaganlar soni")
    total_cut = models.IntegerField(
        default=0, verbose_name="Kesilganlar soni")
    total_sold = models.IntegerField(
        default=0, verbose_name="sotilganlar soni")

    total_sold_price = models.FloatField(
        verbose_name='Umumiy sotilgan narxi', default=0)

    class Meta:
        verbose_name = 'Produkt '
        verbose_name_plural = 'Produktlar'

    def __str__(self):
        return self.name

    def export_excel(self, request):
        products = self.get_queryset(request)

        # Create a new workbook
        workbook = Workbook()
        worksheet = workbook.active

        # Write headers
        # Example headers, adjust as per your model fields
        headers = ['Name', 'Price', 'Quantity']
        worksheet.append(headers)

        # Write data rows
        for product in products:
            # Example data, adjust as per your model fields
            row = [product.name, product.price, product.quantity]
            worksheet.append(row)

        # Set the response headers for file download
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=products.xlsx'

        # Save workbook to response
        workbook.save(response)

        return response


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

    def __str__(self):
        formatted_date = self.date.strftime('%B %Y, %H:%M')
        return f'{self.user} ({formatted_date})'

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
    buyer = models.CharField(max_length=250, verbose_name='Haridor')
    seller = models.CharField(max_length=250, verbose_name='Sotuvchi')
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Xodim')
    date = models.DateTimeField(
        auto_now_add=True, verbose_name='Sotilgan sana')

    class Meta:
        verbose_name = 'Sotuv '
        verbose_name_plural = "Sotuv Bo'limi "

    def __str__(self):
        return self.buyer


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

    def clean(self):
        super().clean()
        if self.product:
            if self.quantity_sold > self.product.total_cut:
                raise ValidationError(
                    "sotilgan qiymat kesilgan qiymatdan oshib ketdi")

    def save(self, *args, **kwargs):
        self.single_sold_price = self.product.price
        self.total_sold_price = self.single_sold_price * self.quantity_sold
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Kesilgan mahsulot'
        verbose_name_plural = 'Kesilgan mahsulotlar'
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

    def clean(self):
        super().clean()
        if self.product:
            if self.quantity_sold > self.product.total_new:
                raise ValidationError(
                    "sotilgan qiymat kesilmagan qiymatdan oshib ketdi")

    def save(self, *args, **kwargs):
        self.single_sold_price = self.product.price
        self.total_sold_price = self.single_sold_price * self.quantity_sold
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Kesilmagan mahsulot'
        verbose_name_plural = 'Kesilmagan mahsulot'
        unique_together = ['product', 'sales']

    def __str__(self):
        return str(self.quantity_sold)+' ta '+self.product.name
