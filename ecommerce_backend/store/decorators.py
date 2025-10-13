import json

def admin_required(func):
    def wrapper(handler, *args, **kwargs):
        if handler.headers.get('Authorization') == 'admin':
            return func(handler, *args, **kwargs)
        else:
            handler.send_response(403) # Forbidden
            handler.send_header('Content-type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": "Acceso denegado. Se requiere rol de administrador."}).encode('utf-8'))
    return wrapper