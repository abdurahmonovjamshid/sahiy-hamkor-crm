from django.contrib import admin
from django.db.models import F, Sum
from django.utils.html import format_html
from mptt.admin import DraggableMPTTAdmin

from .models import Product, Warehouse, Sales


class ProductAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "title"
    list_filter = ('parent',)
    autocomplete_fields = ('parent',)
    search_fields = ('title',)

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('tree_actions', 'indented_title',
                    'highlight_total', 'get_price', 'get_total_price', 'measurement')
        else:
            return ('tree_actions', 'indented_title', 'highlight_total', 'measurement')

    def get_total_price(self, obj):
        if not obj.parent:
            return '-'
        formatted_price = "{:,.1f}".format(obj.total * obj.price)
        return formatted_price+' '+obj.currency

    get_total_price.short_description = 'Mavjud komponent narxi'

    def get_price(self, obj):
        if not obj.parent:
            return '-'
        formatted_price = "{:,.1f}".format(obj.price)
        return formatted_price+' '+obj.currency
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


class WarehouseAdmin(admin.ModelAdmin):
    list_filter = ('arrival_time', 'component')
    date_hierarchy = 'arrival_time'
    ordering = ('-arrival_time',)
    exclude = ('user', 'price', 'total_price')

    # change_list_template = 'admin/warehouse_change_list.html'
    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('__str__', 'get_price', 'user', 'arrival_time')
        else:
            return ('__str__', 'user', 'arrival_time')

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        queryset = self.get_queryset(request)
        total_price = queryset.aggregate(total_price=Sum('total_price'))[
            'total_price'] or 0
        formatted_price = "{:,.1f}".format(total_price)

        try:
            response.context_data['summary_line'] = f"Umumiy narx: {formatted_price}"
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


class SalesAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'buyer', 'get_price', 'user', 'sold_time')
    list_filter = ('sold_time', 'component')
    date_hierarchy = 'sold_time'
    ordering = ('-sold_time',)
    exclude = ('user', 'price', 'total_price')

    # change_list_template = 'admin/warehouse_change_list.html'

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('__str__', 'buyer', 'get_price', 'user', 'sold_time')
        else:
            return ('__str__', 'buyer', 'user', 'sold_time')

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        queryset = self.get_queryset(request)
        total_price = queryset.aggregate(total_price=Sum('total_price'))[
            'total_price'] or 0
        formatted_price = "{:,.1f}".format(total_price)

        try:
            response.context_data['summary_line'] = f"Umumiy narx: {formatted_price}"
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


admin.site.register(Product, ProductAdmin)
admin.site.register(Warehouse, WarehouseAdmin)
admin.site.register(Sales, SalesAdmin)
