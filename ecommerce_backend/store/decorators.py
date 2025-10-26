# store/decorators.py
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, HttpResponse
from functools import wraps
import json

def admin_required(view_func):
    """
    Decorador que verifica si el usuario tiene un rol de administrador 
    y es compatible con las vistas basadas en clases (View) de Django.
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        
        # 🔑 Lógica de Autenticación:
        # En el entorno de Django, el objeto 'request' se pasa directamente.
        
        # **NOTA IMPORTANTE:**
        # Como estás simulando la autenticación con un header, 
        # debemos chequear el header aquí. 
        # En producción, esto se haría verificando request.user.is_staff o request.session.get('user_role').
        
        # Simulando la verificación del header 'Authorization'
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.lower() == 'admin':
            # Si la autenticación es exitosa, ejecuta la función de la vista (get, post)
            return view_func(self, request, *args, **kwargs)
        else:
            # Si falla la autenticación, devolvemos una respuesta 403 de Django
            
            # Prepara el JSON de error
            error_response = json.dumps({"error": "Acceso denegado. Se requiere rol de administrador."})
            
            # Devuelve una respuesta HTTP 403 (Acceso Denegado) compatible con Django
            return HttpResponseForbidden(
                error_response, 
                content_type='application/json' # Especifica el tipo de contenido
            )
            
    return wrapper