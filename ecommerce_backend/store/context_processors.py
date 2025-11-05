# store/context_processors.py

def user_context(request):
    """
    Hace que el 'username' y 'user_role' de la sesión 
    estén disponibles en todas las plantillas.
    """
    return {
        'username': request.session.get('username'),
        'user_role': request.session.get('user_role'),
    }