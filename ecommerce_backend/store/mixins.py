# store/mixins.py
from django.shortcuts import redirect
from django.contrib import messages

# Un "Mixin" es como un "paquete de funcionalidad" que podemos "mezclar"
# con nuestras Vistas Basadas en Clases (VBC).
class AdminRequiredMixin:
    """
    Este Mixin funciona como un guardia de seguridad para las Vistas (HTML).
    
    Cualquier vista que herede de esto (ej: AdminDashboard(AdminRequiredMixin, ...))
    primero ejecutará este código 'dispatch' ANTES de mostrar la página.
    """
    def dispatch(self, request, *args, **kwargs):
        # 'dispatch' es el primer método que se ejecuta en una VBC.
        
        # 1. Revisamos la sesión: ¿El rol del usuario NO es 'admin'?
        if request.session.get('user_role') != 'admin':
            
            # 2. Si no es admin, le mostramos un mensaje de error.
            messages.error(request, "No tienes permiso para acceder a esta página.")
            
            # 3. Lo expulsamos (redirigimos) a la pantalla de 'login'.
            return redirect('login') 

        # 4. Si LLEGAMOS aquí, significa que SÍ es admin.
        #    Dejamos que la vista continúe su ejecución normal.
        return super().dispatch(request, *args, **kwargs)