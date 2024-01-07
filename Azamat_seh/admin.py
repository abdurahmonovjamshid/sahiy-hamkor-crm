from django.http import HttpResponseRedirect
from django.urls import reverse
from django.urls import path
import plotly.graph_objects as go
from django.shortcuts import render
from django import forms
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.db.models import F,  Sum
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from mptt.admin import DraggableMPTTAdmin

from .models import (Component, Product, ProductComponent,
                     ProductProduction, Sales, SalesEvent, Warehouse)


class ComponentAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "title"
    list_filter = ('parent',)
    autocomplete_fields = ('parent',)
    search_fields = ('title',)

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('tree_actions', 'indented_title',
                    'highlight_total', 'get_price', 'get_total_price', 'measurement')
        else:
            return ('tree_actions', 'indented_title',
                    'highlight_total', 'measurement')

    def get_total_price(self, obj):
        if not obj.parent:
            total_child_price = obj.children.annotate(total_price=F(
                'price') * F('total')).aggregate(total=Sum('total_price'))['total']
            return "{:,.2f}".format(total_child_price).rstrip("0").rstrip(".")+'sum'
        formatted_price = "{:,.1f}".format(obj.total * obj.price)
        return formatted_price+' sum'

    get_total_price.short_description = 'Mavjud komponent narxi'

    def get_price(self, obj):
        if not obj.parent:
            return '-'
        formatted_price = "{:,.1f}".format(obj.price)
        return formatted_price+' sum'
    get_price.short_description = 'Narxi'
    get_price.admin_order_field = 'price'

    def highlight_total(self, obj):
        if obj.parent:
            if obj.total < obj.notification_limit:  # Specify your desired threshold value here
                return format_html(
                    '<span style="background-color:#FF0E0E; color:white; padding: 2px 5px;">{}</span>',
                    str(obj.total)+' '+obj.measurement
                )
            return str(obj.total)+' '+obj.measurement
        elif not obj.parent and obj.highlight:
            return format_html('<span style="background-color:#FF0E0E; color:white; padding: 2px 10px;">-</span>')

    highlight_total.short_description = 'Umumiy'
    highlight_total.admin_order_field = 'total'


class ProductComponentInline(admin.TabularInline):
    model = ProductComponent
    extra = 1
    fields = ['component', 'quantity',]
    autocomplete_fields = ['component']
    verbose_name_plural = 'Produkt Komponentlari'
    verbose_name = 'komponent'


class ProductAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "name"
    list_filter = ('parent',)
    autocomplete_fields = ('parent',)
    search_fields = ('name',)
    inlines = [ProductComponentInline]
    list_filter = ['name']
    search_fields = ('name',)

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Umumiy malumot', {
                'fields': ('parent', 'name', 'price', 'total_new',),
            }),
        )
        if not request.user.is_superuser:
            print('/'*88)
            price_fields = ('price',)
            fieldsets[0][1]['fields'] = tuple(
                field for field in fieldsets[0][1]['fields'] if field not in price_fields)
        return fieldsets

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('tree_actions', 'indented_title', 'tannarx', 'get_price', 'get_total_new', 'non_sold_price',)
        else:
            return ('tree_actions', 'indented_title', 'get_total_new',)

    def get_total_new(self, obj):
        if obj.parent:
            return obj.total_new
        else:
            return '-'
    get_total_new.short_description = 'Ishlab chiqarilganlar soni'

    def get_total_sold(self, obj):
        if obj.parent:
            return obj.total_sold
        else:
            return '-'
    get_total_sold.short_description = 'Sotilganlar soni'

    def get_price(self, obj):
        if obj.parent:
            return str(obj.price)+' sum'
        else:
            return '-'
    get_price.short_description = 'Sotuv narxi'

    def non_sold_price(self, obj):
        if obj.parent:
            formatted_price = "{:,.1f}".format(
                obj.price*(obj.total_new))
            return formatted_price+' sum'
        else:
            total_price = obj.children.aggregate(
                total_price=Sum(F('total_new') * F('price')))['total_price']
            return "{:,.1f}".format(total_price)+'sum'
    non_sold_price.short_description = 'Mavjud tovar narxi'

    def tannarx(self, obj):
        if obj.parent:
            product_price = 0
            for productcomponent in obj.productcomponent_set.all():
                product_price += productcomponent.quantity*productcomponent.component.price
            return "{:,.1f}".format(product_price)+' sum'
        else:
            return '-'
    tannarx.short_description = 'Tan narxi'


class ProductProductionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'quantity', 'user', 'date')
    list_filter = ('user', 'product', 'date',)
    readonly_fields = ('user', 'date')
    date_hierarchy = 'date'
    change_list_template = 'admin/production_azamat.html'

    def changelist_view(self, request, extra_context=None):
        if not request.GET and not request.session.get('current_page') == request.path:
            request.session['current_page'] = request.path
            current_month = timezone.now().month
            current_year = timezone.now().year
            return HttpResponseRedirect(
                reverse('admin:Azamat_seh_productproduction_changelist') +
                f'?date__year={current_year}&date__month={current_month}'
            )
        response = super().changelist_view(request, extra_context=extra_context)

        queryset = self.get_queryset(request)

        # Apply filters and search terms to the queryset
        try:
            cl = response.context_data['cl']
            queryset = cl.get_queryset(request)
        except:
            queryset = self.get_queryset(request)

        # Calculate total price

        summary = queryset.values('product__name').annotate(
            total_quantity=Sum(F('quantity')))
        summary_list = {}
        for result in summary:
            product__name = result['product__name']
            total_quantity = result['total_quantity']
            if product__name in summary_list:
                summary_list[product__name] += total_quantity
            else:
                summary_list[product__name] = total_quantity

        sorted_data = sorted(summary_list.items(),
                             key=lambda x: x[1], reverse=True)

        sorted_dict = {item[0]: item[1] for item in sorted_data}

        try:
            response.context_data['total'] = sorted_dict
        except:
            pass

        return response

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        obj.save()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)


class WarehouseAdmin(admin.ModelAdmin):
    list_filter = ('date', 'component')
    date_hierarchy = 'date'
    ordering = ('-date',)
    exclude = ('user', 'price')

    # change_list_template = 'admin/warehouse_change_list.html'

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('__str__', 'get_price', 'user', 'date')
        else:
            return ('__str__', 'user', 'date')

    def changelist_view(self, request, extra_context=None):
        if not request.GET and not request.session.get('current_page') == request.path:
            request.session['current_page'] = request.path
            current_month = timezone.now().month
            current_year = timezone.now().year
            return HttpResponseRedirect(
                reverse('admin:Azamat_seh_warehouse_changelist') +
                f'?date__year={current_year}&date__month={current_month}'
            )
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            cl = response.context_data['cl']
            queryset = cl.get_queryset(request)
        except:
            queryset = self.get_queryset(request)

        total_price = queryset.aggregate(total_price=Sum('price'))[
            'total_price'] or 0
        formatted_price = "{:,.1f}".format(total_price)

        try:
            response.context_data[' summary_line'] = f"Umumiy narx: {formatted_price}"
        except:
            pass
        return response

    def get_price(self, obj):
        formatted_price = "{:,.1f}".format(obj.price)
        return formatted_price+' sum'

    get_price.short_description = 'Narxi'
    get_price.admin_order_field = 'price'

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        obj.save()

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)


class SalesEventInline(admin.TabularInline):
    model = SalesEvent
    extra = 1
    autocomplete_fields = ('sales',)
    readonly_fields = ('single_sold_price', 'total_sold_price', 'profit')
    
    def get_fields(self, request, obj=None):
        fields = ('product', 'quantity_sold',
                  'single_sold_price', 'total_sold_price', 'profit')

        # Check if the user is a superuser
        if not request.user.is_superuser:
            # Remove the 'single_sold_price' and 'total_sold_price' fields from the inline
            fields = tuple(field for field in fields if field not in (
                'single_sold_price', 'total_sold_price', 'profit'))

        return fields


class SalesAdmin(admin.ModelAdmin):
    inlines = [SalesEventInline]
    list_filter = ['buyer', 'seller', 'user', 'date']
    search_fields = ['buyer', 'seller']
    date_hierarchy = 'date'
    # readonly_fields = ('seller',)
    exclude = ('user',)

    change_list_template = 'admin/sales_azamat.html'

    def changelist_view(self, request, extra_context=None):
        if not request.GET and not request.session.get('current_page') == request.path:
            request.session['current_page'] = request.path
            current_month = timezone.now().month
            current_year = timezone.now().year
            return HttpResponseRedirect(
                reverse('admin:Azamat_seh_sales_changelist') +
                f'?date__year={current_year}&date__month={current_month}'
            )
        response = super().changelist_view(request, extra_context=extra_context)

        # Apply filters and search terms to the queryset
        try:
            cl = response.context_data['cl']
            queryset = cl.get_queryset(request)
        except:
            queryset = self.get_queryset(request)

        sales_events = SalesEvent.objects.filter(sales__in=queryset)

        products = sales_events.values('product__name').annotate(
            total_sales=Sum('quantity_sold')
        )
        product_names = [product['product__name'] for product in products]
        total_sales = [product['total_sales'] for product in products]

        fig = go.Figure(data=[go.Bar(x=product_names, y=total_sales)])
        div = fig.to_html(full_html=False)

        # Calculate total price
        total_sold_price = SalesEvent.objects.filter(sales__in=queryset).aggregate(
            total_sold_price=Sum(F('total_sold_price')))['total_sold_price']

        total_profit_price = SalesEvent.objects.filter(sales__in=queryset).aggregate(
            total_profit_price=Sum(F('profit')))['total_profit_price']

        try:
            response.context_data['total'] = "{:,.1f}".format(
                total_sold_price)+'sum'
            response.context_data['graph'] = div
            response.context_data['profit'] = "{:,.1f}".format(
                total_profit_price)+'sum'
        except:
            pass

        return response

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ['buyer', 'seller',
                    'get_sales_events', 'get_total_price', 'get_total_profit', 'user', 'date']
        else:
            return ['buyer', 'seller',
                    'get_sales_events_user', 'user', 'date']

    def get_total_price(self, obj):
        sales_events = obj.selling_cut.all()
        total_price = sum(event.total_sold_price for event in sales_events)

        formatted_price = "{:,.1f}".format(total_price)
        return formatted_price+' sum'
    get_total_price.short_description = 'Umumiy Narx'

    def get_total_profit(self, obj):
        sales_events = obj.selling_cut.all()
        total_price = sum(event.profit for event in sales_events)

        formatted_price = "{:,.1f}".format(total_price)
        return formatted_price+' sum'
    get_total_profit.short_description = 'Umumiy Foyda'

    def get_sales_events(self, obj):
        sales_events = obj.selling_cut.all()
        return ", ".join(str(sale_event)+f' ({sale_event.single_sold_price} sum dan)' for sale_event in sales_events)

    get_sales_events.short_description = 'Ishlab chiqarilgan mahsulotlar'

    def get_sales_events_user(self, obj):
        sales_events = obj.selling_cut.all()
        return ", ".join(str(sale_event) for sale_event in sales_events)

    get_sales_events_user.short_description = 'Ishlab chiqarilgan mahsulotlar'

    def save_model(self, request, obj, form, change):
        # Set the current logged-in user as the seller
        obj.user = request.user
        obj.save()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow superuser to delete
        if request.user.is_superuser:
            return True
        # Restrict regular users from delete
        return False


admin.site.register(Component, ComponentAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductProduction, ProductProductionAdmin)
admin.site.register(Warehouse, WarehouseAdmin)

admin.site.register(Sales, SalesAdmin)
