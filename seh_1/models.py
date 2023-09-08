from django.db import models


class Component(models.Model):
    MEASUREMENT_CHOICES = [
        ('kg', 'Kilogram'),
        ('l', 'Liter'),
        ('pc', 'Piece'),
    ]

    name = models.CharField(max_length=100)
    measurement = models.CharField(max_length=2, choices=MEASUREMENT_CHOICES)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    components = models.ManyToManyField(Component, through='ProductComponent')

    def __str__(self):
        return self.name


class ProductComponent(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.product} - {self.component} ({self.quantity})'
