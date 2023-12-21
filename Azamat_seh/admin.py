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
            return '-'
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
                'fields': ('parent', 'name', 'price', 'total_new', 'total_sold', 'total_sold_price'),
            }),
        )
        if not request.user.is_superuser:
            print('/'*88)
            price_fields = ('price', 'total_sold_price')
            fieldsets[0][1]['fields'] = tuple(
                field for field in fieldsets[0][1]['fields'] if field not in price_fields)
        return fieldsets

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('tree_actions', 'indented_title', 'tannarx', 'get_price', 'get_total_new',
                    'get_total_sold', 'non_sold_price', 'get_total_sold_price', 'profit')
        else:
            return ('tree_actions', 'indented_title', 'get_total_new',
                    'get_total_sold')

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

    def profit(self, obj):
        if obj.parent:
            product_price = 0
            for productcomponent in obj.productcomponent_set.all():
                product_price += productcomponent.quantity*productcomponent.component.price
            product_price = 1.18*product_price

            formatted_price = "{:,.1f}".format(
                obj.total_sold_price - (product_price*obj.total_sold))
            return formatted_price + ' sum'
        else:
            return '-'
    profit.short_description = 'Foyda'

    def get_price(self, obj):
        if obj.parent:
            return str(obj.price)+' sum'
        else:
            return '-'
    get_price.short_description = 'Sotuv narxi'
    get_price.admin_order_field = 'price'

    def non_sold_price(self, obj):
        if obj.parent:
            formatted_price = "{:,.1f}".format(
                obj.price*(obj.total_new))
            return formatted_price+' sum'
        else:
            return '-'
    non_sold_price.short_description = 'Mavjud tovar narxi'
    non_sold_price.admin_order_field = 'non_sold_price'

    def tannarx(self, obj):
        if obj.parent:
            product_price = 0
            for productcomponent in obj.productcomponent_set.all():
                product_price += productcomponent.quantity*productcomponent.component.price
            return "{:,.1f}".format(product_price*1.18)+' sum'
        else:
            return '-'
    tannarx.short_description = 'Tan narxi'
    tannarx.admin_order_field = 'single_product_price'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            single_product_price= Sum(
                F('productcomponent__quantity') * F('productcomponent__component__price')*1.18)
        )
        queryset = queryset.annotate(
            non_sold_price= Sum(
                F('price') * F('total_new'))
        )
        return queryset

    def get_total_sold_price(self, obj):
        if obj.parent:
            formatted_price = "{:,.1f}".format(obj.total_sold_price)
            return formatted_price+' sum'
        else:
            return '-'
    get_total_sold_price.short_description = "Sotilgan tovar narxi"
    get_total_sold_price.admin_order_field = 'total_sold_price'

    # change_list_template = 'admin/product_change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        queryset = self.get_queryset(request)
        total_price = queryset.aggregate(total_price= Sum('total_sold_price'))[
            'total_price'] or 0
        formatted_price = "{:,.1f}".format(total_price)

        total_product_price = queryset.aggregate(total_product_price= Sum(F('total_new')*F('price')))[
            'total_product_price'] or 0
        formatted_pr_price = "{:,.1f}".format(total_product_price)

        try:
            response.context_data[
                ' summary_line'] = f"Umumiy sotilgan tovarlar narxi: {formatted_price} sum<hr>Umumiy mavjud tovarlar narxi: {formatted_pr_price} sum"
        except:
            pass
        return response


class ProductProductionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'quantity', 'user', 'production_date')
    list_filter = ('user', 'product', 'production_date',)
    readonly_fields = ('user', 'production_date')
    date_hierarchy = 'production_date'
    # change_list_template = 'admin/production_change_list.html'

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        obj.save()

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     current_month = timezone.now().month
    #     current_year = timezone.now().year

    #     return qs.filter(production_date__month=current_month, production_date__year=current_year)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)


class WarehouseAdmin(admin.ModelAdmin):
    list_filter = ('arrival_time', 'component')
    date_hierarchy = 'arrival_time'
    ordering = ('-arrival_time',)
    exclude = ('user', 'price')

    # change_list_template = 'admin/warehouse_change_list.html'

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('__str__', 'get_price', 'user', 'arrival_time')
        else:
            return ('__str__', 'user', 'arrival_time')

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        queryset = self.get_queryset(request)
        total_price = queryset.aggregate(total_price= Sum('price'))[
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
    readonly_fields = ('single_sold_price', 'total_sold_price')

    def get_fields(self, request, obj=None):
        fields = ('product', 'quantity_sold',
                  'single_sold_price', 'total_sold_price')

        # Check if the user is a superuser
        if not request.user.is_superuser:
            # Remove the 'single_sold_price' and 'total_sold_price' fields from the inline
            fields = tuple(field for field in fields if field not in (
                'single_sold_price', 'total_sold_price'))

        return fields


class SalesAdmin(admin.ModelAdmin):
    inlines = [SalesEventInline]
    list_filter = ['buyer', 'seller', 'user', 'date']
    search_fields = ['buyer', 'seller']
    date_hierarchy = 'date'
    # readonly_fields = ('seller',)
    exclude = ('user',)

    # change_list_template = 'admin/sales_change_list.html'

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ['buyer', 'seller',
                    'get_sales_events', 'get_total_price', 'user', 'date']
        else:
            return ['buyer', 'seller',
                    'get_sales_events_user', 'user', 'date']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            total_price= Sum('selling_cut__total_sold_price')
        )
        return queryset

    def get_total_price(self, obj):
        sales_events = obj.selling_cut.all()
        total_price =  sum(event.total_sold_price for event in sales_events)

        formatted_price = "{:,.1f}".format(total_price)
        return formatted_price+' sum'

    get_total_price.short_description = 'Narx'
    get_total_price.admin_order_field = 'total_price'

    def get_sales_events(self, obj):
        sales_events = obj.selling_cut.all()
        return ", ".join(str(sale_event)+f' ({sale_event.single_sold_price} sum dan)' for sale_event in sales_events)

    get_sales_events.short_description = 'Kesilgan mahsulotlar'

    def get_sales_events_user(self, obj):
        sales_events = obj.selling_cut.all()
        return ", ".join(str(sale_event) for sale_event in sales_events)

    get_sales_events_user.short_description = 'Kesilgan mahsulotlar'

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
