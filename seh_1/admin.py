from django import forms
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import F, Sum
from django.utils import timezone

from .models import (Component, Product, ProductComponent, ProductProduction,
                     Warehouse)


class ComponentAdmin(admin.ModelAdmin):
    # Add the fields to search for autocomplete functionality
    search_fields = ['name']
    list_filter = ('measurement',)
    list_display = ('name', 'total',
                    'measurement')
    ordering = ('total',)


class ProductComponentInline(admin.TabularInline):
    model = ProductComponent
    extra = 1
    fields = ['component', 'quantity',]
    autocomplete_fields = ['component']
    verbose_name_plural = 'Produkt Komponentlari'
    verbose_name = 'komponent'


class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductComponentInline]
    list_display = ('name', 'get_made_product_count')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            get_made_product_count=Sum('productproduction__quantity'))
        return queryset

    def get_made_product_count(self, obj):
        return obj.get_made_product_count or 0

    get_made_product_count.short_description = 'kesilmaganlar soni'
    get_made_product_count.admin_order_field = 'get_made_product_count'


class ProductProductionAdmin(admin.ModelAdmin):
    list_display = ('series', 'product', 'quantity', 'user', 'production_date')
    list_filter = ('user', 'product', 'production_date')
    exclude = ('user',)
    date_hierarchy = 'production_date'
    ordering = ('-production_date',)

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        current_month = timezone.now().month
        current_year = timezone.now().year

        return qs.filter(production_date__month=current_month, production_date__year=current_year)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)


class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'arrival_time')
    list_filter = ('arrival_time', 'component')
    date_hierarchy = 'arrival_time'
    ordering = ('-arrival_time',)


admin.site.register(Component, ComponentAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductProduction, ProductProductionAdmin)
admin.site.register(Warehouse, WarehouseAdmin)
