import json
import os
from .models import Cart, CartItem

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARTS_FILE = os.path.join(BASE_DIR, 'data', 'carts.json') # Esta es la variable correcta

class CartService:
    def __init__(self):
        # AHORA SÍ USA LA VARIABLE GLOBAL
        self._ensure_data_file_exists(CARTS_FILE) 

    def _ensure_data_file_exists(self, file_path): # Le pasamos la ruta
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                # Inicializa el JSON como un objeto vacío {} (para carritos de usuarios)
                json.dump({}, f)

    def get_cart(self, user_id):
        with open(CARTS_FILE, 'r', encoding='utf-8') as f: # USA CARTS_FILE
            try:
                carts = json.load(f)
            except json.JSONDecodeError:
                carts = {} # Si el archivo está corrupto o vacío, empieza de nuevo
            
            if str(user_id) in carts:
                return Cart.from_dict(carts[str(user_id)])
        return Cart(user_id=user_id)

    def save_cart(self, cart):
        # Carga todos los carritos
        try:
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                carts = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            carts = {}
        
        # Actualiza solo el carrito del usuario específico
        carts[str(cart.user_id)] = cart.to_dict()
        
        # Vuelve a escribir el archivo COMPLETO
        with open(CARTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(carts, f, indent=4, ensure_ascii=False)

    def remove_cart(self, user_id):
        """Eliminar el carrito de un usuario"""
        try:
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                carts = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            carts = {}
            
        if str(user_id) in carts:
            del carts[str(user_id)]
            
        with open(CARTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(carts, f, indent=4, ensure_ascii=False)