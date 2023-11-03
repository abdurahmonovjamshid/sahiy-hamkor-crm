from django.db.models.signals import post_delete, post_save, pre_save
from . models import Warehouse, Sales, Product
from django.dispatch import receiver


@receiver(post_save, sender=Warehouse)
def warehouse_add(sender, instance, created, **kwargs):
    if created:
        component = instance.component
        component.total += instance.quantity
        component.save()


@receiver(pre_save, sender=Warehouse)
def warehouse_presave(sender, instance, **kwargs):
    if instance.pk:
        old_warehouse = Warehouse.objects.get(pk=instance.pk)
        component = instance.component
        component.total = component.total - old_warehouse.quantity + instance.quantity
        component.save()


@receiver(post_delete, sender=Warehouse)
def warehouse_delete(sender, instance, **kwargs):
    component = instance.component
    component.total -= instance.quantity
    component.save()


@receiver(post_save, sender=Sales)
def sales_add(sender, instance, created, **kwargs):
    if created:
        component = instance.component
        component.total -= instance.quantity
        component.save()


@receiver(pre_save, sender=Sales)
def sales_presave(sender, instance, **kwargs):
    if instance.pk:
        old_warehouse = Sales.objects.get(pk=instance.pk)
        component = instance.component
        component.total = component.total + old_warehouse.quantity - instance.quantity
        component.save()


@receiver(post_delete, sender=Sales)
def sales_delete(sender, instance, **kwargs):
    component = instance.component
    component.total += instance.quantity
    component.save()
