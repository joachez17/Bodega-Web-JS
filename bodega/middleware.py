# bodega/middleware.py

import threading

_thread_locals = threading.local()

def get_current_user():
    """Devuelve el usuario logueado actualmente."""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """
    Middleware que guarda el usuario de cada petición en una variable
    accesible globalmente (pero segura para cada hilo/petición).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = request.user
        response = self.get_response(request)
        return response