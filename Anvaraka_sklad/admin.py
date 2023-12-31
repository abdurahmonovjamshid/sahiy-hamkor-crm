from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db.models import Case, F, Sum, Value, When
from django.utils import timezone
from datetime import datetime
from django.utils.safestring import mark_safe
from django.contrib import admin
from django.db.models import F, Sum
from django.utils.html import format_html
from mptt.admin import DraggableMPTTAdmin
from django.db import models

from .models import Product, Warehouse, Sales, ProductComponent, SalesEvent, Selling


class ProductComponentInline(admin.TabularInline):
    model = ProductComponent
    extra = 1
    fields = ['product', 'quantity', 'quantity_in_measurement',]
    autocomplete_fields = ['product']
    verbose_name_plural = 'Produkt Komponentlari'
    verbose_name = 'komponent'


class ProductAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "title"
    list_filter = ('parent',)
    autocomplete_fields = ('parent',)
    search_fields = ('title',)
    inlines = [ProductComponentInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'parent', 'price', 'sell_price', 'currency', 'measurement', 'total', 'notification_limit')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (None, {
                'fields': ('title', 'parent', 'price', 'sell_price', 'currency', 'measurement', 'total', 'notification_limit')
            }),
        )
        if not request.user.is_superuser:
            price_fields = ('price', 'sell_price', 'currency')
            fieldsets[0][1]['fields'] = tuple(
                field for field in fieldsets[0][1]['fields'] if field not in price_fields)
        return fieldsets

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('tree_actions', 'indented_title',
                    'highlight_total', 'get_price', 'get_sell_price', 'get_total_price', 'get_total_sell_price', 'get_benefit', 'measurement')
        else:
            return ('tree_actions', 'indented_title', 'highlight_total', 'measurement')

    def get_benefit(self, obj):
        if not obj.parent:
            return '-'
        formatted_price = "{:,.1f}".format(
            obj.total * (obj.sell_price-obj.price))
        return formatted_price+' '+obj.currency
    get_benefit.short_description = 'Foyda'

    def get_total_price(self, obj):
        if not obj.parent:
            nmadur = obj.children.aggregate(
                sum=Sum(Case(
                    When(currency='sum', then=F('price')*F('total')),
                    default=0,
                    output_field=models.FloatField()
                )),
                usd=Sum(Case(
                    When(currency='$', then=F('price')*F('total')),
                    default=0,
                    output_field=models.FloatField()
                ))
            )
            formatted_prices = ''
            if nmadur['sum'] != 0.0:
                formatted_prices += "{:,.1f}".format(nmadur['sum'])+'sum '
            if nmadur['usd'] != 0.0:
                formatted_prices += "{:,.1f}".format(nmadur['usd'])+'$ '
            return formatted_prices
        formatted_price = "{:,.1f}".format(obj.total * obj.price)
        return formatted_price+' '+obj.currency

    get_total_price.short_description = 'Umumiy narxi'

    def get_total_sell_price(self, obj):
        if not obj.parent:
            return '-'
        formatted_price = "{:,.1f}".format(obj.total * obj.sell_price)
        return formatted_price+' '+obj.currency

    get_total_sell_price.short_description = 'Umumiy sotuv narxi'

    def get_price(self, obj):
        if not obj.parent:
            return '-'
        formatted_price = "{:,.1f}".format(obj.price)
        return formatted_price+' '+obj.currency

    get_price.short_description = 'Narxi'
    get_price.admin_order_field = 'price'

    def get_sell_price(self, obj):
        if not obj.parent:
            return '-'
        formatted_price = "{:,.1f}".format(obj.sell_price)
        return formatted_price+' '+obj.currency

    get_sell_price.short_description = 'Sotuv Narxi'
    get_sell_price.admin_order_field = 'sell_price'

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


class WarehouseAdmin(admin.ModelAdmin):
    list_filter = ('arrival_time', 'component')
    date_hierarchy = 'arrival_time'
    ordering = ('-arrival_time',)
    exclude = ('user', 'price', 'total_price')

    change_list_template = 'admin/warehouse_anvar.html'

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('__str__', 'get_price', 'user', 'arrival_time')
        else:
            return ('__str__', 'user', 'arrival_time')

    def changelist_view(self, request, extra_context=None):
        if not request.GET and not request.session.get('current_page') == request.path:
            request.session['current_page'] = request.path
            current_month = timezone.now().month
            current_year = timezone.now().year
            return HttpResponseRedirect(
                reverse('admin:Anvaraka_sklad_warehouse_changelist') +
                f'?arrival_time__year={current_year}&arrival_time__month={current_month}'
            )
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            cl = response.context_data['cl']
            queryset = cl.get_queryset(request)
        except:
            queryset = self.get_queryset(request)

        # Calculate total prices for each currency
        currency_totals = queryset.values('component__currency').annotate(
            total_price=Sum('total_price'))

        # Create a dictionary to store the formatted currency totals
        formatted_currency_totals = {}
        for currency_total in currency_totals:
            currency = currency_total['component__currency']
            total_price = currency_total['total_price'] or 0
            if currency in formatted_currency_totals:
                formatted_currency_totals[currency] += total_price
            else:
                formatted_currency_totals[currency] = total_price

        for currency, total_price in formatted_currency_totals.items():
            formatted_price = "{:,.1f}".format(total_price)
            formatted_currency_totals[currency] = formatted_price

        try:
            response.context_data['currency_totals'] = formatted_currency_totals
        except:
            pass

        return response

    def get_price(self, obj):
        formatted_price = "{:,.1f}".format(obj.total_price)
        return formatted_price+' '+obj.component.currency

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


class SalesEventtInline(admin.TabularInline):
    model = SalesEvent
    extra = 1
    fields = ['price', 'currency', 'paid']
    autocomplete_fields = ['selling']
    readonly_fields = ['paid']
    verbose_name_plural = 'To\'lovlar '
    verbose_name = 'to\'lov'


class SalesInline(admin.TabularInline):
    model = Sales
    extra = 1
    readonly_fields = ['total_price', 'profit']
    autocomplete_fields = ['selling']
    verbose_name_plural = 'Sotilgan tovarlar '
    verbose_name = 'tovarlar'

    def get_fields(self, request, obj=None):
        fields = ('component', 'quantity',
                  'quantity_in_measurement', 'total_price', 'profit')

        # Check if the user is a superuser
        if not request.user.is_superuser:
            # Remove the 'single_sold_price' and 'total_sold_price' fields from the inline
            fields = tuple(field for field in fields if field not in (
                'total_price', 'profit'))

        return fields

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        if obj:
            return False
        else:
            return True


class SellingAdmin(admin.ModelAdmin):
    list_filter = ('sold_time', 'buyer', 'user')
    date_hierarchy = 'sold_time'
    inlines = [SalesInline, SalesEventtInline]
    search_fields = ['buyer']
    exclude = ('user', 'sold_time')

    change_list_template = 'admin/sales_anvar.html'

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('buyer', 'get_sold_products', 'total_price', 'get_paid', 'user', 'sold_time')
        else:
            return ('buyer', 'get_sold_products_user', 'user', 'sold_time')

    def get_sold_products(self, obj):
        sales = obj.sales_set.values(
            'component__title', 'component__currency', 'component__measurement').annotate(
                total_price=Sum('total_price')).annotate(
                profit=Sum('profit')).annotate(total_measurement=Sum(F('quantity')*F('quantity_in_measurement')))
        return mark_safe("<br>".join(f"{text['total_measurement']}{text['component__measurement']} {text['component__title']} - {text['total_price']:,.1f}{text['component__currency']} - ({text['profit']:,.1f}{text['component__currency']})"
                                     for text in sales
                                     ))

    def get_sold_products_user(self, obj):
        sales = obj.sales_set.all()
        return "; ".join(
            f"{text}" for text in sales
        )

    def changelist_view(self, request, extra_context=None):
        if not request.GET and not request.session.get('current_page') == request.path:
            request.session['current_page'] = request.path
            current_month = timezone.now().month
            current_year = timezone.now().year
            return HttpResponseRedirect(
                reverse('admin:Anvaraka_sklad_selling_changelist') +
                f'?sold_time__year={current_year}&sold_time__month={current_month}'
            )
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            cl = response.context_data['cl']
            queryset = cl.get_queryset(request)
        except:
            queryset = self.get_queryset(request)

        # Calculate total prices for each currency
        currency_totals = queryset.values('sales__component__currency').annotate(
            total_price=Sum('sales__total_price'))

        # Create a dictionary to store the formatted currency totals
        formatted_currency_totals = {}
        for currency_total in currency_totals:
            currency = currency_total['sales__component__currency']
            total_price = currency_total['total_price'] or 0
            if currency in formatted_currency_totals:
                formatted_currency_totals[currency] += total_price
            else:
                formatted_currency_totals[currency] = total_price

        for currency, total_price in formatted_currency_totals.items():
            formatted_price = "{:,.1f}".format(total_price)
            formatted_currency_totals[currency] = formatted_price

        try:
            response.context_data['currency_totals'] = formatted_currency_totals
        except:
            pass

        ############ profit ############
        currency_totals = queryset.values('sales__component__currency').annotate(
            total_price=Sum('sales__profit'))

        # Create a dictionary to store the formatted currency totals
        formatted_currency_totals = {}
        for currency_total in currency_totals:
            currency = currency_total['sales__component__currency']
            total_price = currency_total['total_price'] or 0
            if currency in formatted_currency_totals:
                formatted_currency_totals[currency] += total_price
            else:
                formatted_currency_totals[currency] = total_price

        for currency, total_price in formatted_currency_totals.items():
            formatted_price = "{:,.1f}".format(total_price)
            formatted_currency_totals[currency] = formatted_price

        try:
            response.context_data['currency_profits'] = formatted_currency_totals
        except:
            pass

        return response

    def get_paid(self, obj):
        return obj.get_total_price_by_currency()

        return total_paid

    get_paid.short_description = "To'langan"

    def total_price(self, obj):
        return obj.total_price()

        return total_paid

    total_price.short_description = "Umumiy narx(lar)"

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


admin.site.register(Product, ProductAdmin)
admin.site.register(Warehouse, WarehouseAdmin)
admin.site.register(Selling, SellingAdmin)
