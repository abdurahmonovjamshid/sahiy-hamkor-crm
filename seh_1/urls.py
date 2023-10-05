from django.urls import path
from . import views

urlpatterns = [
    # Existing URL patterns ...
    path('product/export-excel/', views.export_excel, name='product_export_excel'),
]