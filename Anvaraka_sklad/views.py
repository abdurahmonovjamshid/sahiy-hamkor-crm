from django.db.models.signals import post_delete, post_save, pre_save
from . models import Warehouse, Sales, Product, ProductComponent, Selling
from django.dispatch import receiver

sales = Selling.objects.all()

for sale in sales:
    sale.buyer = sale.buyer.title()
    sale.save()


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

        # Calculate the cumulative quantities
        total_quantity = instance.quantity * instance.quantity_in_measurement

        # Update the component totals
        component.total -= total_quantity
        component.save()

        try:
            product_component = component.component.get(
                quantity_in_measurement=instance.quantity_in_measurement)

            # Calculate the cumulative quantities for the product component
            product_component.quantity -= instance.quantity
            if product_component.quantity < 0:
                product_component.quantity = 0

            product_component.save()

        except ProductComponent.DoesNotExist:
            pass

        # Perform cumulative calculations for subsequent Sales instances
        sales_instances = Sales.objects.filter(
            component=component, selling=instance.selling)
        sales_instances = sales_instances.exclude(pk=instance.pk)

        for sales_instance in sales_instances:
            total_quantity += sales_instance.quantity * \
                sales_instance.quantity_in_measurement

            component.total -= sales_instance.quantity * \
                sales_instance.quantity_in_measurement
            component.save()

        # Update the instance's total_price based on the cumulative quantities
        instance.total_price = instance.price * total_quantity
        instance.save()


@receiver(pre_save, sender=Sales)
def sales_presave(sender, instance, **kwargs):
    if instance.pk:
        old_sales = Sales.objects.get(pk=instance.pk)
        component = instance.component
        component.total = component.total + \
            (old_sales.quantity*old_sales.quantity_in_measurement) - \
            (instance.quantity*instance.quantity_in_measurement)
        component.save()

        if old_sales.component.component.filter(quantity_in_measurement=old_sales.quantity_in_measurement):
            product_component = old_sales.component.component.get(
                quantity_in_measurement=old_sales.quantity_in_measurement)

            product_component.quantity += old_sales.quantity
            product_component.save()

        if instance.component.component.filter(quantity_in_measurement=instance.quantity_in_measurement):
            product_component = instance.component.component.get(
                quantity_in_measurement=instance.quantity_in_measurement)
            product_component.quantity -= instance.quantity

            if product_component.quantity < 0:
                product_component.quantity = 0
            product_component.save()


@receiver(post_delete, sender=Sales)
def sales_delete(sender, instance, **kwargs):
    component = instance.component
    component.total += instance.quantity * instance.quantity_in_measurement
    component.save()

    if component.component.filter(quantity_in_measurement=instance.quantity_in_measurement):
        product_component = component.component.get(
            quantity_in_measurement=instance.quantity_in_measurement)
        product_component.quantity += instance.quantity
        product_component.save()
