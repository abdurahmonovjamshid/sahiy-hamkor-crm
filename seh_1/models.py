from django.contrib.auth.models import User
from django.db import models


class Component(models.Model):
    MEASUREMENT_CHOICES = [
        ('kg', 'Kilogram'),
        ('l', 'Litr'),
        ('pc', 'Dona'),
    ]

    name = models.CharField(max_length=100, verbose_name='Nomi')
    measurement = models.CharField(
        max_length=2, choices=MEASUREMENT_CHOICES, verbose_name="O'lchov birligi")

    total = models.FloatField(default=0, verbose_name='umumiy')

    class Meta:
        verbose_name = 'Komponent '
        verbose_name_plural = 'Komponentlar'

    def __str__(self):
        return self.name + f' ({self.get_measurement_display()})'


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nomi')
    components = models.ManyToManyField(
        Component, through='ProductComponent', verbose_name='Komponentlar')

    class Meta:
        verbose_name = 'Produkt '
        verbose_name_plural = 'Produktlar'

    def __str__(self):
        return self.name


class ProductComponent(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='product')
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE, verbose_name="Komponent")
    quantity = models.FloatField(verbose_name="miqdor")

    class Meta:
        unique_together = ('product', 'component')

    def __str__(self):
        return f'({self.quantity} {self.component.get_measurement_display()})'


class ProductProduction(models.Model):
    STATUS_CHOICES = [
        ('kesilgan', 'Kesilgan'),
        ('kesilmagan', 'Kesilmagan'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='xodim', null=True, blank=True)

    series = models.CharField(max_length=50, verbose_name="Seriya")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='Produkt')
    quantity = models.PositiveIntegerField()
    production_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='kesilmagan')

    class Meta:
        verbose_name = 'Tovar '
        verbose_name_plural = 'Ishlab Chiqarilgan Tovarlar'

    def __str__(self):
        formatted_date = self.production_date.strftime('%B %Y, %H:%M')
        return f'{self.quantity} {self.product} ({formatted_date})'


class Warehouse(models.Model):
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE, verbose_name='Komponent')
    quantity = models.IntegerField(verbose_name="Miqdor")
    arrival_time = models.DateTimeField(
        auto_now_add=True, verbose_name='Keltirilgan sana')

    class Meta:
        verbose_name = 'Keltirilgan Komponentlar '
        verbose_name_plural = 'Ombor'

    def __str__(self):
        return f"{self.quantity}{self.component.get_measurement_display()} - {self.component.name}"
