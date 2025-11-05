# store/mixins.py
from django.shortcuts import redirect
from django.contrib import messages

class AdminRequiredMixin:
    """
    Mixin para Vistas Basadas en Clases (HTML) que verifica si el 
    usuario en la sesión es 'admin'.
    Si no lo es, lo redirige al Login.
    """
    def dispatch(self, request, *args, **kwargs):
        # Verificar el rol en la sesión
        if request.session.get('user_role') != 'admin':
            messages.error(request, "No tienes permiso para acceder a esta página.")
            return redirect('login') # Redirige a la vista de login

        # Si es admin, continúa normalmente
        return super().dispatch(request, *args, **kwargs)