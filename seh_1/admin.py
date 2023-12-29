from django.http import HttpResponseRedirect
from django.urls import reverse
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
from django.contrib import messages

from .models import (Component, CuttingEvent, Product, ProductComponent,
                     ProductProduction, ProductReProduction, Sales, SalesEvent,
                     SalesEvent2, Warehouse)
from .views import export_warehouse_excel


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name',
                    'last_name', 'is_staff', 'last_login')

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
    list_filter = ('parent',)
    autocomplete_fields = ('parent',)
    search_fields = ('title',)

    change_list_template = 'admin/component_change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        # queryset = self.get_queryset(request)
        cl = response.context_data['cl']
        queryset = cl.get_queryset(request)

        total_price = queryset.aggregate(total_price=Sum(F('price')*F('total')))[
            'total_price'] or 0
        formatted_price = "{:,.2f}".format(total_price).rstrip("0").rstrip(".")

        try:
            response.context_data[
                'summary_line'] = f"Mavjud komponent narxi: {formatted_price}$"
        except:
            pass
        return response

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Umumiy malumot', {
                'fields': ('parent', 'title', 'price', 'measurement', 'total', 'notification_limit'),
            }),
        )
        if not request.user.is_superuser:
            print('/'*88)
            price_fields = ('price', )
            fieldsets[0][1]['fields'] = tuple(
                field for field in fieldsets[0][1]['fields'] if field not in price_fields)
        return fieldsets

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
            return "{:,.2f}".format(total_child_price).rstrip("0").rstrip(".")+'$'
        formatted_price = "{:,.2f}".format(
            obj.total * obj.price).rstrip("0").rstrip(".")
        return formatted_price+'$'

    get_total_price.short_description = 'Mavjud komponent narxi'

    def get_price(self, obj):
        if not obj.parent:
            return '-'
        formatted_price = "{:,.2f}".format(obj.price).rstrip("0").rstrip(".")
        return formatted_price+'$'
    get_price.short_description = 'Narxi'
    get_price.admin_order_field = 'price'

    def highlight_total(self, obj):
        if obj.parent:
            if obj.total < obj.notification_limit:  # Specify your desired threshold value here
                return format_html(
                    '<span style="background-color:#FF0E0E; color:white; padding: 2px 5px;">{}</span>',
                    str(obj.total)+' '+obj.measurement
                )
            return "{:,.1f}".format(obj.total).rstrip("0").rstrip(".")+' '+obj.measurement
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
    list_filter = ['name']
    search_fields = ('name',)

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Umumiy malumot', {
                'fields': ('name', 'price', 'total_new', 'total_cut', 'total_sold', 'total_sold_price'),
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
            return ('name', 'tannarx', 'get_price', 'total_new', 'total_cut',
                    'total_sold', 'non_sold_price', 'get_total_sold_price', 'profit')
        else:
            return ('name', 'total_new', 'total_cut',
                    'total_sold')

    def profit(self, obj):
        product_price = 0
        for productcomponent in obj.productcomponent_set.all():
            product_price += productcomponent.quantity*productcomponent.component.price
        product_price = 1.18*product_price

        formatted_price = "{:,.2f}".format(
            obj.total_sold_price - (product_price*obj.total_sold))
        return formatted_price + '$'
    profit.short_description = 'Foyda'

    def get_price(self, obj):
        return "{:,.2f}".format(obj.price).rstrip("0").rstrip(".")+'$'
    get_price.short_description = 'Sotuv narxi'
    get_price.admin_order_field = 'price'

    def non_sold_price(self, obj):
        formatted_price = "{:,.2f}".format(
            obj.price*(obj.total_new+obj.total_cut)).rstrip("0").rstrip(".")
        return formatted_price+'$'
    non_sold_price.short_description = 'Mavjud tovar narxi'
    non_sold_price.admin_order_field = 'non_sold_price'

    def tannarx(self, obj):
        product_price = 0
        for productcomponent in obj.productcomponent_set.all():
            product_price += productcomponent.quantity*productcomponent.component.price
        return "{:,.2f}".format(product_price*1.18)+'$'
    tannarx.short_description = 'Tan narxi'
    tannarx.admin_order_field = 'single_product_price'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            single_product_price=Sum(
                F('productcomponent__quantity') * F('productcomponent__component__price')*1.18)
        )
        queryset = queryset.annotate(
            non_sold_price=Sum(
                F('price') * (F('total_new')+F('total_cut')))
        )
        return queryset

    def get_total_sold_price(self, obj):
        formatted_price = "{:,.2f}".format(
            obj.total_sold_price).rstrip("0").rstrip(".")
        return formatted_price+'$'
    get_total_sold_price.short_description = "Sotilgan tovar narxi"
    get_total_sold_price.admin_order_field = 'total_sold_price'

    change_list_template = 'admin/product_change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        # queryset = self.get_queryset(request)
        cl = response.context_data['cl']
        queryset = cl.get_queryset(request)

        total_price = queryset.aggregate(total_price=Sum('total_sold_price'))[
            'total_price'] or 0
        formatted_price = "{:,.2f}".format(total_price).rstrip("0").rstrip(".")

        total_product_price = queryset.aggregate(total_product_price=Sum((F('total_new') + F('total_cut'))*F('price')))[
            'total_product_price'] or 0
        formatted_pr_price = "{:,.2f}".format(
            total_product_price).rstrip("0").rstrip(".")

        try:
            response.context_data[
                'summary_line'] = f"Umumiy sotilgan tovarlar narxi: {formatted_price}$<hr>Umumiy mavjud tovarlar narxi: {formatted_pr_price}$"
        except:
            pass
        return response


class ProductProductionAdmin(admin.ModelAdmin):
    search_fields = ('title',)

    list_display = ('get_title', 'quantity', 'user', 'date')
    list_filter = ('user', 'product', 'date', 'series')
    readonly_fields = ('user', 'date',)
    # exclude = ['cutting_complate']
    date_hierarchy = 'date'
    list_display_links = ('get_title',)
    change_list_template = 'admin/production_change_list.html'

    def changelist_view(self, request, extra_context=None):
        current_month = timezone.now().month
        current_year = timezone.now().year

        # Redirect to the current month's view
        if not request.GET:
            url = reverse('admin:seh_1_productproduction_changelist')
            url += f'?date__year={current_year}&date__month={current_month}'
            return HttpResponseRedirect(url)

        return super().changelist_view(request, extra_context)

    def get_title(self, instance):
        return f'{instance.series}-{instance.product}'
    get_title.short_description = 'Title'

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
    list_filter = ('arrival_time', 'component')
    date_hierarchy = 'arrival_time'
    ordering = ('-arrival_time',)
    exclude = ('user', 'price')

    change_list_template = 'admin/warehouse_change_list.html'

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('__str__', 'get_price', 'user', 'arrival_time')
        else:
            return ('__str__', 'user', 'arrival_time')

    def changelist_view(self, request, extra_context=None):
        if not request.GET:
            current_month = timezone.now().month
            current_year = timezone.now().year
            return HttpResponseRedirect(
                reverse('admin:seh_1_warehouse_changelist') +
                f'?arrival_time__year={current_year}&arrival_time__month={current_month}'
            )

        response = super().changelist_view(request, extra_context=extra_context)

        cl = response.context_data['cl']
        queryset = cl.queryset

        total_price = queryset.aggregate(total_price=Sum('price'))[
            'total_price'] or 0
        formatted_price = "{:,.2f}".format(total_price).rstrip("0").rstrip(".")

        try:
            response.context_data['summary_line'] = f"Umumiy narx: {formatted_price}"
        except KeyError:
            pass

        return response

    def get_price(self, obj):
        formatted_price = "{:,.2f}".format(obj.price).rstrip("0").rstrip(".")
        return formatted_price+'$'

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


class CuttingEventInline(admin.TabularInline):
    model = CuttingEvent
    extra = 1
    fields = ('product', 'quantity_cut')
    autocomplete_fields = ('product_reproduction',)


class ProductReProductionAdmin(admin.ModelAdmin):
    inlines = [CuttingEventInline]
    list_display = ['user', 'total_cut',
                    'get_cutting_events', 'date']
    search_fields = ['user__username']
    list_filter = ['user', 'date']
    date_hierarchy = 'date'
    readonly_fields = ('user', 'date')

    change_list_template = 'admin/reproduction_change_list.html'

    def changelist_view(self, request, extra_context=None):
        current_month = timezone.now().month
        current_year = timezone.now().year

        # Redirect to the current month's view
        if not request.GET:
            url = reverse('admin:seh_1_productreproduction_changelist')
            url += f'?date__year={current_year}&date__month={current_month}'
            return HttpResponseRedirect(url)

        return super().changelist_view(request, extra_context)

    def get_cutting_events(self, obj):
        cutting_events = obj.cutting.all()
        return ", ".join(str(str(cutting_event.quantity_cut) + ' ta ' + cutting_event.product.name) for cutting_event in cutting_events)
    get_cutting_events.short_description = 'Kesilgan  mahsulotlar'

    def total_cut(self, obj):
        total_cut = 0
        for cuttingevent in obj.cutting.all():
            total_cut += cuttingevent.quantity_cut
        return total_cut

    total_cut.short_description = 'Umumiy kesilganlar'
    total_cut.admin_order_field = 'total_cut'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(total_cut=Sum('cutting__quantity_cut'))
        return queryset

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        return False
    # Add other desired configurations for the admin view


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


class SalesEventInline2(admin.TabularInline):
    model = SalesEvent2
    extra = 1
    fields = ('product', 'quantity_sold')
    readonly_fields = ('total_sold_price', 'single_sold_price')
    autocomplete_fields = ('sales',)

    def get_queryset(self, request):
        current_month = timezone.now().month
        current_year = timezone.now().year
        queryset = super().get_queryset(request)

        # Check if any filter is already applied
        if not request.GET:
            queryset = queryset.filter(
                date__year=current_year, date__month=current_month)

        return queryset

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
    inlines = [SalesEventInline, SalesEventInline2]
    list_filter = ['buyer', 'seller', 'user', 'date']
    search_fields = ['buyer', 'seller']
    date_hierarchy = 'date'
    # readonly_fields = ('seller',)
    exclude = ('user',)

    change_list_template = 'admin/sales_change_list.html'

    def changelist_view(self, request, extra_context=None):
        current_month = timezone.now().month
        current_year = timezone.now().year

        # Redirect to the current month's view
        if not request.GET:
            url = reverse('admin:seh_1_sales_changelist')
            url += f'?date__year={current_year}&date__month={current_month}'
            return HttpResponseRedirect(url)

        return super().changelist_view(request, extra_context)

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ['buyer', 'seller',
                    'get_sales_events', 'get_sales_event2s', 'get_total_price', 'user', 'date']
        else:
            return ['buyer', 'seller',
                    'get_sales_events_user', 'get_sales_event2s_user', 'user', 'date']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            total_price=Sum('selling_cut__total_sold_price') +
            Sum('selling__total_sold_price')
        )
        return queryset

    def get_total_price(self, obj):
        sales_events = obj.selling_cut.all()
        total_price = sum(event.total_sold_price for event in sales_events)

        sales_events2 = obj.selling.all()
        total_price2 = sum(event.total_sold_price for event in sales_events2)
        formatted_price = "{:,.2f}".format(
            total_price + total_price2).rstrip("0").rstrip(".")
        return formatted_price+'$'

    get_total_price.short_description = 'Narx'
    get_total_price.admin_order_field = 'total_price'

    def get_sales_events(self, obj):
        sales_events = obj.selling_cut.all()
        return ", ".join(str(sale_event)+f' ({sale_event.single_sold_price}$ dan)' for sale_event in sales_events)

    get_sales_events.short_description = 'Kesilgan mahsulotlar'

    def get_sales_events_user(self, obj):
        sales_events = obj.selling_cut.all()
        return ", ".join(str(sale_event) for sale_event in sales_events)

    get_sales_events_user.short_description = 'Kesilgan mahsulotlar'

    def get_sales_event2s(self, obj):
        sales_event2s = obj.selling.all()
        return ", ".join(str(sale_event2)+f' ({sale_event2.single_sold_price}$ dan)' for sale_event2 in sales_event2s)

    get_sales_event2s.short_description = 'Kesilmagan mahsulotlar'

    def get_sales_event2s_user(self, obj):
        sales_event2s = obj.selling.all()
        return ", ".join(str(sale_event2) for sale_event2 in sales_event2s)

    get_sales_event2s_user.short_description = 'Kesilmagan mahsulotlar'

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


admin.site.register(ProductReProduction, ProductReProductionAdmin)

admin.site.register(Component, ComponentAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductProduction, ProductProductionAdmin)
admin.site.register(Warehouse, WarehouseAdmin)

admin.site.register(Sales, SalesAdmin)
