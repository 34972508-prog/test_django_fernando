# ecommerce_backend/urls.py (Archivo principal)
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... otras rutas como 'admin/' ...
    path('store/', include('store.urls')), 
    
    # 🎯 CORRECCIÓN CLAVE: Esto mapea /api/ a las rutas de tu app 'store'
    path('api/', include('store.urls')), 
]

# NECESARIO para servir imágenes en DESARROLLO (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)