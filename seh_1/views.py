from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import ProductProduction, Warehouse


@receiver(post_save, sender=ProductProduction)
def subtract_component_total(sender, instance, created, **kwargs):
    if created:
        product_components = instance.product.productcomponent_set.all()
        for product_component in product_components:
            total_quantity_by_component = product_component.quantity * \
                instance.quantity
            component = product_component.component
            component.total -= total_quantity_by_component
            component.save()


# @receiver(pre_save, sender=ProductProduction)
# def edit_component_total(sender, instance, **kwargs):
#     if instance.pk:
#         old_instance = ProductProduction.objects.get(pk=instance.pk)
#         product_components = old_instance.product.productcomponent_set.all()
#         for product_component in product_components:
#             old_quantity_by_component = product_component.quantity * old_instance.quantity
#             component = product_component.component
#             component.total += old_quantity_by_component
#             component.save()
#             print(component.total)

#     product_components = instance.product.productcomponent_set.all()
#     for product_component in product_components:
#         new_quantity_by_component = product_component.quantity * instance.quantity
#         component = product_component.component
#         component.total -= new_quantity_by_component
#         component.save()


@receiver(post_delete, sender=ProductProduction)
def delete_component_total(sender, instance, **kwargs):
    product_components = instance.product.productcomponent_set.all()
    for product_component in product_components:
        total_quantity_by_component = product_component.quantity * \
            instance.quantity
        component = product_component.component
        component.total += total_quantity_by_component
        component.save()


@receiver(post_save, sender=Warehouse)
def add_component_total(sender, instance, created, **kwargs):
    if created:
        print("qo'shildi" * 88)
        component = instance.component
        component.total += instance.quantity
        component.save()


@receiver(pre_save, sender=Warehouse)
def update_component_total_on_edit(sender, instance, **kwargs):
    if instance.pk:
        # Warehouse object is being edited (not a new object)
        old_warehouse = Warehouse.objects.get(pk=instance.pk)
        component = instance.component
        component.total = component.total - old_warehouse.quantity + instance.quantity
        component.save()


@receiver(post_delete, sender=Warehouse)
def update_component_total_on_delete(sender, instance, **kwargs):
    component = instance.component
    component.total -= instance.quantity
    component.save()
