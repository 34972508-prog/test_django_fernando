from django.urls import path
from django.views.generic import TemplateView
from .views import ProductListCreateAPIView, ProductDetailAPIView, AdminProductView, ProductFormView, DeleteProductHTMLView # Importa la nueva vista



urlpatterns = [
    # Solución: La ruta ahora debe ser 'store/index.html' debido a la subcarpeta 'store/'
    # dentro de 'templates/' (ver estructura de archivos).
    path('', TemplateView.as_view(template_name='store/index.html'), name='home'),
    
    # Añadida ruta explícita para /home, apuntando a la ruta corregida.
    path('home/', TemplateView.as_view(template_name='store/index.html'), name='home_explicit'),
    
    # URLs existentes para la API/Administración
    path('products/', ProductListCreateAPIView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('admin-view/', AdminProductView.as_view(), name='admin-product-view'),

    path('product/new/', ProductFormView.as_view(), name='product-create'),
    path('product/edit/<int:pk>/', ProductFormView.as_view(), name='product-edit'),
    path('product/delete/<int:pk>/', DeleteProductHTMLView.as_view(), name='product-delete-html'),
]