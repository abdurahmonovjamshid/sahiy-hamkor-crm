from django import forms
from django.contrib import admin

from .models import Component, Product, ProductComponent


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement')


# @admin.register(ProductComponent)
# class ProductComponentAdmin(admin.ModelAdmin):
#     list_display = ('product', 'component', 'quantity')


class ProductComponentInline(admin.TabularInline):
    model = ProductComponent
    extra = 1


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name']


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    inlines = [ProductComponentInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        # Update the quantity for each ProductComponent
        for formset in formsets:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()


admin.site.register(Product, ProductAdmin)
