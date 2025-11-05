# store/decorators.py
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, HttpResponse
from functools import wraps
import json

def admin_required(view_func):
    """
    Decorador que verifica si el ROL DE ADMIN está en la SESIÓN de Django.
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        
        # --- NUEVA LÓGICA DE SESIÓN ---
        
        # Verificamos el rol guardado en la sesión
        user_role = request.session.get('user_role', None)
        
        if user_role == 'admin':
            # Si es 'admin', ejecuta la función de la vista (get, post)
            return view_func(self, request, *args, **kwargs)
        else:
            # Si no es admin (o no está logueado), devolvemos 403
            
            error_response = json.dumps({"error": "Acceso denegado. Se requiere rol de administrador."})
            
            # Devuelve una respuesta HTTP 403 (Acceso Denegado)
            return HttpResponseForbidden(
                error_response, 
                content_type='application/json'
            )
            
    return wrapper