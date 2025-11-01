from django.urls import path
from django.views.generic import TemplateView
from .views import ProductListCreateAPIView, ProductDetailAPIView, AdminProductView,\
    ProductFormView, DeleteProductHTMLView, List_productView,\
    ProductDetailHTMLView 
from django.conf import settings
from django.conf.urls.static import static



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

    # Nuevas rutas para el usuario final en HTML
    path('products/list', List_productView.as_view(), name='product-list-html'),  # Nueva ruta para listar productos en HTML
    path('products/<int:pk>/view/', ProductDetailHTMLView.as_view(), name='product-detail-html'),  # ruta detalle HTML
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

