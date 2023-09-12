from django import forms
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import F, Sum
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from mptt.admin import DraggableMPTTAdmin

from .models import (Component, Product, ProductComponent, ProductProduction,
                     Warehouse)


class CustomUserAdmin(UserAdmin):

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        # Hide "Permissions" fieldset for non-superusers
        if not request.user.is_superuser:
            fieldsets = [
                (None, {'fields': ('username', 'password')}),
                (_('Personal info'), {
                 'fields': ('first_name', 'last_name', 'email')}),
            ]

        return fieldsets

    def get_queryset(self, request):
        # Get the queryset based on the user
        queryset = super().get_queryset(request)

        # Exclude superusers from any filtering
        if not request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)

        return queryset

    def has_change_permission(self, request, obj=None):
        # Allow users to change their own profile
        if obj is not None and not request.user.is_superuser:
            return obj == request.user

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Restrict users from deleting any user
        if obj is not None and not request.user.is_superuser:
            return False

        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # Block non-superusers from making themselves superusers
        if not request.user.is_superuser and obj.is_superuser:
            obj.is_superuser = False

        super().save_model(request, obj, form, change)


admin.site.unregister(User)  # Unregister the default UserAdmin
# Register with the custom CustomUserAdmin
admin.site.register(User, CustomUserAdmin)


class ComponentAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "title"
    list_display = ('tree_actions', 'indented_title',
                    'highlight_total', 'measurement')
    list_filter = ('parent',)
    autocomplete_fields = ('parent',)
    search_fields = ('title',)

    def highlight_total(self, obj):
        if obj.parent:
            if obj.total < obj.notification_limit:  # Specify your desired threshold value here
                return format_html(
                    '<span style="background-color:#FF0E0E; color:white; padding: 2px 5px;">{}</span>',
                    obj.total
                )
            return obj.total
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


class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductComponentInline]
    list_display = ('name', 'total_new', 'total_cut', 'total_sold')




class ProductProductionAdmin(admin.ModelAdmin):
    list_display = ('series', 'product', 'quantity', 'total_cut',
                    'total_sold', 'user', 'production_date')
    list_filter = ('user', 'product', 'production_date')
    exclude = ('user', 'total_cut', 'total_sold')
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
    list_display = ('__str__', 'user', 'arrival_time')
    list_filter = ('arrival_time', 'component')
    date_hierarchy = 'arrival_time'
    ordering = ('-arrival_time',)
    exclude = ('user',)

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


admin.site.register(Component, ComponentAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductProduction, ProductProductionAdmin)
admin.site.register(Warehouse, WarehouseAdmin)
