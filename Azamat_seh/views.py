from datetime import datetime

import requests
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.http import HttpResponse
from django.urls import reverse
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from pytz import timezone

from conf import settings

from .models import (Product, ProductProduction, Sales, SalesEvent, Warehouse)


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


@receiver(post_delete, sender=ProductProduction)
def delete_component_total(sender, instance, **kwargs):
    product_components = instance.product.productcomponent_set.all()
    product = instance.product
    product.total_new -= instance.quantity
    product.save()

    for product_component in product_components:
        total_quantity_by_component = product_component.quantity * instance.quantity
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


@receiver(post_save, sender=SalesEvent)
def sales_create(sender, instance, created, **kwargs):
    if created:
        try:
            product = instance.product
            product.total_new -= instance.quantity_sold
            product.total_sold += instance.quantity_sold
            product.total_sold_price += instance.total_sold_price
            product.save()

        except Exception as e:
            print(e)


@receiver(post_delete, sender=SalesEvent)
def sales_delete(sender, instance, **kwargs):
    try:
        product = instance.product
        product.total_new += instance.quantity_sold
        product.total_sold -= instance.quantity_sold
        product.total_sold_price -= instance.total_sold_price
        product.save()

        sales = instance.sales
        if sales.selling_cut.all().count() == 0:
            sales.delete()
    except Exception as e:
        print(e)
