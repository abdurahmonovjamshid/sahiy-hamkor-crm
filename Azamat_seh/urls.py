from django.urls import path

from . import views

urlpatterns = [
    # Existing URL patterns ...
    path('sales/export-excel/', views.sales_excel_export,
         name='sales_excel_export'),
]
