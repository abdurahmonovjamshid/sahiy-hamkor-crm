from django.urls import path

from . import views

urlpatterns = [
    # Existing URL patterns ...
    path('product/export-excel/', views.component_export_excel,
         name='component_export_excel'),
    path('product/export-excel/', views.export_excel,
         name='product_export_excel'),
    path('warehouse/export-excel/', views.export_warehouse_excel,
         name='warehouse_export_excel'),
    path('production/export-excel/', views.export_production_excel,
         name='production_export_excel'),
    path('reproduction/export-excel/', views.export_reproduction_excel,
         name='reproduction_export_excel'),
    path('sales/export-excel/', views.export_sales_excel,
         name='sales_export_excel'),
]
