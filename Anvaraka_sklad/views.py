from django.db.models.signals import post_delete, post_save, pre_save
from . models import Warehouse, Sales, Product, ProductComponent
from django.dispatch import receiver


@receiver(post_save, sender=Warehouse)
def warehouse_add(sender, instance, created, **kwargs):
    if created:
        component = instance.component
        component.total += instance.quantity * instance.quantity_in_measurement
        component.save()

        ######## product component ##########
        product_component, created = ProductComponent.objects.get_or_create(
            product=instance.component, quantity_in_measurement=instance.quantity_in_measurement)

        if not created:
            product_component.quantity += instance.quantity
            product_component.save()
        else:
            product_component.quantity = instance.quantity
            product_component.save()


@receiver(pre_save, sender=Warehouse)
def warehouse_presave(sender, instance, **kwargs):
    if instance.pk:
        old_warehouse = Warehouse.objects.get(pk=instance.pk)

        component = instance.component
        component.total = component.total - \
            (old_warehouse.quantity*old_warehouse.quantity_in_measurement) + \
            (instance.quantity*instance.quantity_in_measurement)
        component.save()

        if old_warehouse.component.component.filter(quantity_in_measurement=old_warehouse.quantity_in_measurement):
            product_component = old_warehouse.component.component.get(
                quantity_in_measurement=old_warehouse.quantity_in_measurement)

            product_component.quantity -= old_warehouse.quantity
            if product_component.quantity < 0:
                product_component.quantity = 0
            product_component.save()

        product_component, created = ProductComponent.objects.get_or_create(
            product=instance.component, quantity_in_measurement=instance.quantity_in_measurement)

        if not created:
            product_component.quantity += instance.quantity
            product_component.save()
        else:
            product_component.quantity = instance.quantity
            product_component.save()


@receiver(post_delete, sender=Warehouse)
def warehouse_delete(sender, instance, **kwargs):
    component = instance.component
    component.total -= (instance.quantity*instance.quantity_in_measurement)
    component.save()

    if instance.component.component.filter(quantity_in_measurement=instance.quantity_in_measurement):
        product_component = instance.component.component.get(
            quantity_in_measurement=instance.quantity_in_measurement)
        product_component.quantity -= instance.quantity
        if product_component.quantity < 0:
            product_component.quantity = 0
        product_component.save()


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
