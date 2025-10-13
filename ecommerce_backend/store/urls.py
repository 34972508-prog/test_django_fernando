# store/urls.py
from django.urls import path
#from .views import ProductListCreateAPIView, ProductDetailAPIView

from .views import ProductListCreateAPIView, ProductDetailAPIView, AdminProductView # Importa la nueva vista


urlpatterns = [
    path('products/', ProductListCreateAPIView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('admin-view/', AdminProductView.as_view(), name='admin-product-view'),
]