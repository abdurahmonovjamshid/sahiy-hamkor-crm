from django import forms
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import F, Sum

from .models import Component, Product, ProductComponent, ProductProduction


class ComponentAdmin(admin.ModelAdmin):
    # Add the fields to search for autocomplete functionality
    search_fields = ['name']
    list_display = ('name', 'measurement')


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
    list_display = ('series', 'product', 'quantity', 'production_date')
    list_filter = ('product', 'production_date')
    ordering = ('production_date',)


admin.site.register(Component, ComponentAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductProduction, ProductProductionAdmin)
