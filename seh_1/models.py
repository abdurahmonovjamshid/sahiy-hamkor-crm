from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


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
    measurement = models.CharField(
        max_length=2, choices=MEASUREMENT_CHOICES, verbose_name="O'lchov birligi")

    total = models.FloatField(default=0, verbose_name='umumiy')
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
    components = models.ManyToManyField(
        Component, through='ProductComponent', verbose_name='Komponentlar', limit_choices_to={'parent__isnull': False})

    total_new = models.IntegerField(
        default=0, verbose_name="Kesilmaganlar soni")
    total_cut = models.IntegerField(
        default=0, verbose_name="Kesilganlar soni")
    total_sold = models.IntegerField(
        default=0, verbose_name="sotilganlar soni")

    class Meta:
        verbose_name = 'Produkt '
        verbose_name_plural = 'Produktlar'

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
        User, on_delete=models.SET_NULL, verbose_name='xodim', null=True, blank=True)

    series = models.CharField(max_length=50, verbose_name="Seriya")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='Produkt')
    quantity = models.PositiveIntegerField(verbose_name="Kesilmaganlar soni")
    total_cut = models.IntegerField(
        default=0, verbose_name="Kesilganlar soni")
    total_sold = models.IntegerField(
        default=0, verbose_name="sotilganlar soni")

    production_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Ishlab chiqarilish vaqti')

    class Meta:
        verbose_name = 'Tovar '
        verbose_name_plural = 'Ishlab Chiqarilgan Tovarlar'

    def __str__(self):
        local_production_date = timezone.localtime(self.production_date)
        formatted_date = local_production_date.strftime('%D, %H:%M')
        return f'{self.series}-{self.product} ({formatted_date})'


class Warehouse(models.Model):
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE, verbose_name='Komponent', limit_choices_to={'parent__isnull': False})
    quantity = models.IntegerField(verbose_name="Miqdor")
    arrival_time = models.DateTimeField(
        auto_now_add=True, verbose_name='Keltirilgan sana')

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='xodim')

    class Meta:
        verbose_name = 'Keltirilgan Komponentlar '
        verbose_name_plural = 'Ombor'

    def __str__(self):
        return f"{self.quantity}{self.component.get_measurement_display()} - {self.component.title}"
