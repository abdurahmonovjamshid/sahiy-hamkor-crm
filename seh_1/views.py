from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.http import HttpResponse
from openpyxl import Workbook

from .models import (CuttingEvent, Product, ProductProduction, SalesEvent,
                     SalesEvent2, Warehouse)


def export_excel(request):
    products = Product.objects.all()

    # Create a new workbook
    workbook = Workbook()
    worksheet = workbook.active

    # Write headers
    headers = ['Nomi', 'Kesilmaganlar soni', 'Kesilganlar soni',
               'Sotilganlar soni', 'Umumiy sotilgan narxi']
    worksheet.append(headers)

    # Write data rows
    for product in products:
        row = [
            product.name,
            product.total_new,
            product.total_cut,
            product.total_sold,
            "{:,.1f}".format(product.total_sold_price)
        ]
        worksheet.append(row)

    # Set the response headers for file download
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=products.xlsx'

    # Save workbook to response
    workbook.save(response)

    return response


@receiver(post_save, sender=ProductProduction)
def subtract_component_total(sender, instance, created, **kwargs):
    if created:
        product_components = instance.product.productcomponent_set.all()
        product = instance.product
        product.total_new += instance.quantity
        product.save()

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
    product = instance.product
    product.total_new -= instance.quantity + \
        instance.total_cut + instance.total_sold
    product.save()

    for product_component in product_components:
        total_quantity_by_component = product_component.quantity * \
            (instance.quantity + instance.total_cut + instance.total_sold)
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


@receiver(post_save, sender=CuttingEvent)
def curring_create(sender, instance, created, **kwargs):
    if created:
        try:
            pr_production = instance.product_production
            pr_production.quantity -= instance.quantity_cut
            pr_production.total_cut += instance.quantity_cut
            pr_production.save()

            product = pr_production.product
            product.total_new -= instance.quantity_cut
            product.total_cut += instance.quantity_cut
            product.save()

        except Exception as e:
            print(e)


@receiver(post_delete, sender=CuttingEvent)
def cutting_delete(sender, instance, **kwargs):
    try:

        pr_production = instance.product_production
        pr_production.quantity += instance.quantity_cut + instance.quantity_sold
        pr_production.total_cut -= instance.quantity_cut + instance.quantity_sold
        pr_production.save()

        product = pr_production.product
        product.total_new += instance.quantity_cut + instance.quantity_sold
        product.total_cut -= instance.quantity_cut + instance.quantity_sold
        product.save()
        product_reproduction = instance.product_reproduction
        if product_reproduction.cutting.all().count() == 0:
            product_reproduction.delete()
    except Exception as e:
        print(e)


@receiver(post_save, sender=SalesEvent)
def sales_create(sender, instance, created, **kwargs):
    if created:
        try:
            cuttingevent = instance.cut_product
            cuttingevent.quantity_cut -= instance.quantity_sold
            cuttingevent.quantity_sold += instance.quantity_sold
            cuttingevent.save()

            pr_production = cuttingevent.product_production
            pr_production.total_cut -= instance.quantity_sold
            pr_production.total_sold += instance.quantity_sold
            pr_production.save()

            product = pr_production.product
            product.total_cut -= instance.quantity_sold
            product.total_sold += instance.quantity_sold
            product.total_sold_price += instance.total_sold_price
            product.save()

        except Exception as e:
            print(e)


@receiver(post_delete, sender=SalesEvent)
def sales_delete(sender, instance, **kwargs):
    try:
        cuttingevent = instance.cut_product
        cuttingevent.quantity_cut += instance.quantity_sold
        cuttingevent.quantity_sold -= instance.quantity_sold
        cuttingevent.save()

        pr_production = cuttingevent.product_production
        pr_production.total_cut += instance.quantity_sold
        pr_production.total_sold -= instance.quantity_sold
        pr_production.save()

        product = pr_production.product
        product.total_cut += instance.quantity_sold
        product.total_sold -= instance.quantity_sold
        product.total_sold_price -= instance.total_sold_price
        product.save()

        sales = instance.sales
        if sales.selling_cut.all().count() == 0 and sales.selling.all().count() == 0:
            sales.delete()
    except Exception as e:
        print(e)


@receiver(post_save, sender=SalesEvent2)
def sales2_create(sender, instance, created, **kwargs):
    if created:
        try:
            pr_production = instance.non_cut_product
            pr_production.quantity -= instance.quantity_sold
            pr_production.total_sold += instance.quantity_sold
            pr_production.save()

            product = pr_production.product
            product.total_new -= instance.quantity_sold
            product.total_sold += instance.quantity_sold
            product.total_sold_price += instance.total_sold_price
            product.save()
        except Exception as e:
            print(e)


@receiver(post_delete, sender=SalesEvent2)
def sales2_delete(sender, instance, **kwargs):
    try:
        pr_production = instance.non_cut_product
        pr_production.quantity += instance.quantity_sold
        pr_production.total_sold -= instance.quantity_sold
        pr_production.save()

        product = pr_production.product
        product.total_new += instance.quantity_sold
        product.total_sold -= instance.quantity_sold
        product.total_sold_price -= instance.total_sold_price
        product.save()

        sales = instance.sales
        if sales.selling_cut.all().count() == 0 and sales.selling.all().count() == 0:
            sales.delete()
    except Exception as e:
        print(e)
