# ecommerce_backend/urls.py (Archivo principal)
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls), # Asumiendo que esta existe
    
    # 🔑 NUEVA LÍNEA CLAVE: Mapea la URL raíz (/) a todas las rutas de la app 'store'.
    path('', include('store.urls')), 
    
    # Si estas rutas ya están en store.urls y apuntan al inicio, pueden ser redundantes:
    # path('store/', include('store.urls')), 
    
    path('api/', include('store.urls')),
]

# NECESARIO para servir imágenes en DESARROLLO (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)