from django.urls import path
from django.views.generic import TemplateView

# Importamos TODAS las vistas necesarias desde views.py
from .views import (
    ProductListCreateAPIView, ProductDetailAPIView, AdminProductView,
    ProductFormView, DeleteProductHTMLView, List_productView,
    ProductDetailHTMLView, CartView, AdminCategoryView, CategoryFormView, 
    DeleteCategoryView, CheckoutView, LoginView, RegisterView, LogoutView, 
    profile_view, AdminUserView, DeleteUserHTMLView,
    
    AdminBranchView # <-- ¡LA NUEVA VISTA!
)

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rutas principales
    path('', TemplateView.as_view(template_name='store/index.html'), name='home'),
    path('home/', TemplateView.as_view(template_name='store/index.html'), name='home_explicit'),
    
    # API de Productos (referenciadas en el decorador)
    path('products/', ProductListCreateAPIView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    
    # Administración de Productos (HTML)
    path('admin-view/', AdminProductView.as_view(), name='admin-product-view'),
    path('product/new/', ProductFormView.as_view(), name='product-create'),
    path('product/edit/<int:pk>/', ProductFormView.as_view(), name='product-edit'),
    path('product/delete/<int:pk>/', DeleteProductHTMLView.as_view(), name='product-delete-html'),

    # Administración de Usuarios (HTML)
    path('admin/users/', AdminUserView.as_view(), name='admin-user-view'), 
    path('admin/user/delete/<int:pk>/', DeleteUserHTMLView.as_view(), name='admin-user-delete'),

    # Administración de Categorías (HTML)
    path('categories/list/', AdminCategoryView.as_view(), name='admin-category-view'),
    path('category/new/', CategoryFormView.as_view(), name='category-create'),
    path('category/edit/<int:pk>/', CategoryFormView.as_view(), name='category-edit'),
    path('category/delete/<int:pk>/', DeleteCategoryView.as_view(), name='category-delete-html'),
   
    # --- NUEVA RUTA DE SUCURSALES ---
    path('admin/branches/', AdminBranchView.as_view(), name='admin-branch-view'),

    # Vistas de Cliente (HTML)
    path('products/list', List_productView.as_view(), name='product-list-html'),
    path('products/<int:pk>/view/', ProductDetailHTMLView.as_view(), name='product-detail-html'),

    # Autenticación
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'),
    
    # Carrito y Checkout
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-confirmation/', TemplateView.as_view(template_name='store/confirmacion_pago.html'), name='order-confirmation'),
]

# Configuración para archivos estáticos y media en DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)