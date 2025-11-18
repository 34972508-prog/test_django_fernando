# store/decorators.py
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, HttpResponse
from functools import wraps
import json

def admin_required(view_func):
    """
    Este es nuestro "Decorador" de seguridad.
    
    Funciona como un "guardia" que ponemos en la puerta de una vista.
    Si lo usamos (ej: @admin_required), esta función se ejecuta PRIMERO.
    
    Comprueba si el rol 'admin' está guardado en la sesión de Django.
    """
    
    # @wraps nos ayuda a que la vista "decorada" siga manteniendo
    # su nombre original, lo cual es bueno para depurar.
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        
        # --- LÓGICA DE SEGURIDAD ---
        
        # 1. Revisamos la sesión del usuario para ver qué rol tiene.
        user_role = request.session.get('user_role', None)
        
        # 2. ¿Es administrador?
        if user_role == 'admin':
            # ¡Sí! Le damos permiso.
            # Ejecutamos la función de la vista original (get, post, etc.)
            return view_func(self, request, *args, **kwargs)
        else:
            # 3. ¡No es admin! (O no ha iniciado sesión).
            
            # Preparamos una respuesta de error clara en formato JSON.
            error_response = json.dumps({"error": "Acceso denegado. Se requiere rol de administrador."})
            
            # Devolvemos un error 403 (Acceso Prohibido).
            # La vista original NUNCA se ejecuta.
            return HttpResponseForbidden(
                error_response, 
                content_type='application/json'
            )
            
    # El decorador devuelve la función "envuelta" (el 'wrapper').
    return wrapper