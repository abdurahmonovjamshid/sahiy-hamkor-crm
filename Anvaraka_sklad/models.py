from mptt.models import MPTTModel
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class Product(MPTTModel):
    MEASUREMENT_CHOICES = [
        ('kg', 'Kilogram'),
        ('l', 'Litr'),
        ('m', 'Metr'),
        ('ta', 'Dona'),
    ]

    CURRENCY_CHOICES = [
        ('sum', 'So\'m'),
        ('$', 'USD')
    ]

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, verbose_name="Bo'limlar",
                               limit_choices_to={'parent__isnull': True},
                               related_name='children', null=True, blank=True, )

    title = models.CharField(max_length=100, verbose_name='Nomi')
    price = models.FloatField(verbose_name='Narxi')
    sell_price = models.FloatField(verbose_name='Sotuv narxi')
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, verbose_name="Valyuta birligi", default='$')

    measurement = models.CharField(
        max_length=2, choices=MEASUREMENT_CHOICES, verbose_name="O'lchov birligi")

    total = models.FloatField(default=0, verbose_name='Umumiy')
    notification_limit = models.IntegerField(
        default=500, verbose_name="Ogohlantirish")

    class Meta:
        verbose_name = 'Mahsulot '
        verbose_name_plural = 'Mahsulotlar'

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


class ProductComponent(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='product', related_name='component')

    quantity = models.IntegerField(verbose_name="Dona", default=0)
    quantity_in_measurement = models.FloatField(
        verbose_name="Miqdor", unique=True)

    def __str__(self):
        return f'({self.quantity} ta {self.quantity_in_measurement}'


class Warehouse(models.Model):
    component = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='Keltirilgan mahsulot ', limit_choices_to={'parent__isnull': False})

    quantity = models.IntegerField(verbose_name="Dona")
    quantity_in_measurement = models.FloatField(verbose_name="Miqdor")

    price = models.FloatField(default=0, verbose_name='Narxi')
    total_price = models.FloatField(default=0, verbose_name='Umumiy narxi')
    arrival_time = models.DateTimeField(
        auto_now_add=True, verbose_name='Keltirilgan sana')

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='xodim', related_name='warehoueeeper')

    class Meta:
        verbose_name = 'Keltirilgan Mahsulot '
        verbose_name_plural = 'Ombor'

    def __str__(self):
        return f"{self.quantity * self.quantity_in_measurement} {self.component.get_measurement_display()} - {self.component.title}"

    def save(self, *args, **kwargs):
        self.price = self.component.price
        self.total_price = self.price * self.quantity * self.quantity_in_measurement
        super().save(*args, **kwargs)


class Sales(models.Model):
    component = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='Sotilgan mahsulot ', limit_choices_to={'parent__isnull': False})
    buyer = models.CharField(max_length=100, verbose_name='Xaridor')

    quantity = models.IntegerField(verbose_name="Dona")
    quantity_in_measurement = models.FloatField(verbose_name="Miqdor")

    price = models.FloatField(default=0, verbose_name='Narxi')
    total_price = models.FloatField(default=0, verbose_name='Umumiy narxi')
    sold_time = models.DateTimeField(
        auto_now_add=True, verbose_name='Sotilgan sana')

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='xodim', related_name='salsekeeper')

    class Meta:
        verbose_name = 'Sotilgan Mahsulot '
        verbose_name_plural = 'Sotuv'

    def __str__(self):
        return f"{self.quantity*self.quantity_in_measurement} {self.component.get_measurement_display()} - {self.component.title}"

    def save(self, *args, **kwargs):
        self.price = self.component.sell_price
        self.total_price = self.price * self.quantity*self.quantity_in_measurement
        super().save(*args, **kwargs)
