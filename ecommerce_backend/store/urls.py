from django.urls import path
from django.views.generic import TemplateView

# Importamos TODAS las vistas necesarias desde views.py

from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rutas principales
    path('', views.HomeView.as_view(), name='home'),
    #path('', TemplateView.as_view(template_name='store/index.html'), name='home'),
    path('home/', views.HomeView.as_view(), name='home_explicit'),
    
    
    # API de Productos (referenciadas en el decorador)
    path('products/', views.ProductListCreateAPIView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
    
    # Administración de Productos (HTML)
    path('admin-view/', views.AdminProductView.as_view(), name='admin-product-view'),
    path('product/new/', views.ProductFormView.as_view(), name='product-create'),
    path('product/edit/<int:pk>/', views.ProductFormView.as_view(), name='product-edit'),
    path('product/delete/<int:pk>/', views.DeleteProductHTMLView.as_view(), name='product-delete-html'),

    # Administración de Usuarios (HTML)
    path('admin/users/', views.AdminUserView.as_view(), name='admin-user-view'), 
    path('admin/user/delete/<int:pk>/', views.DeleteUserHTMLView.as_view(), name='admin-user-delete'),

    # Administración de Categorías (HTML)
    path('categories/list/', views.AdminCategoryView.as_view(), name='admin-category-view'),
    path('category/new/', views.CategoryFormView.as_view(), name='category-create'),
    path('category/edit/<int:pk>/', views.CategoryFormView.as_view(), name='category-edit'),
    path('category/delete/<int:pk>/', views.DeleteCategoryView.as_view(), name='category-delete-html'),
   
    # --- NUEVA RUTA DE SUCURSALES ---
    path('admin/branches/', views.AdminBranchView.as_view(), name='admin-branch-view'),
    path('admin/products/filter/set/', views.SetAdminBranchFilterView.as_view(), name='admin-set-branch-filter'),
    path('admin/products/filter/clear/', views.ClearAdminBranchFilterView.as_view(), name='admin-clear-branch-filter'),
    path('set-branch/', views.SetBranchView.as_view(), name='set-branch'),  # Ruta para establecer la sucursal seleccionada
    path('clear-branch/', views.ClearBranchView.as_view(), name='clear-branch'), # Ruta para limpiar la sucursal seleccionada
    

    # Vistas de Cliente (HTML)
    path('products/list', views.List_productView.as_view(), name='product-list-html'),
    path('products/<int:pk>/view/', views.ProductDetailHTMLView.as_view(), name='product-detail-html'),

    # Autenticación
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Carrito y Checkout
    path('cart/', views.CartView.as_view(), name='cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('order-confirmation/', TemplateView.as_view(template_name='store/confirmacion_pago.html'), name='order-confirmation'),
]

# Configuración para archivos estáticos y media en DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)