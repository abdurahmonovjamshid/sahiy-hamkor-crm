from django.urls import path

from . import views

urlpatterns = [
    # Existing URL patterns ...
    path('production/export-excel/', views.azamat_production_excel,
         name='azamat_production_excel'),
    path('sales/export-excel/', views.sales_excel_export,
         name='sales_excel_export'),
]
