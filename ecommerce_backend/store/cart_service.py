# store/cart_service.py
import json
import os
from .models import Cart, CartItem

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 
# ESTA ES LA VARIABLE GLOBAL QUE DEBEMOS USAR
CARTS_FILE = os.path.join(BASE_DIR, 'data', 'carts.json') 

class CartService:
    def __init__(self):
        # Usamos la variable global CARTS_FILE
        self._ensure_data_file_exists(CARTS_FILE) 

    def _ensure_data_file_exists(self, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f) # Inicializa como un objeto vacío

    def get_cart(self, user_id):
        # Usamos la variable global CARTS_FILE
        self._ensure_data_file_exists(CARTS_FILE)
        
        try:
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                carts = json.load(f)
        except json.JSONDecodeError:
            carts = {}
            
        if str(user_id) in carts:
            cart_data = carts[str(user_id)]
            # Asegurarse de que 'items' exista
            if 'items' not in cart_data:
                cart_data['items'] = {}
            return Cart.from_dict(cart_data)
        
        return Cart(user_id=user_id)
    
    def get_all_carts(self):
        """
        Carga y devuelve TODOS los carritos del archivo JSON.
        Devuelve un diccionario {user_id: cart_data}
        """
        self._ensure_data_file_exists(CARTS_FILE)
        
        try:
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                carts = json.load(f)
        except json.JSONDecodeError:
            carts = {}
        
        return carts

    def save_cart(self, cart):
        os.makedirs(os.path.dirname(CARTS_FILE), exist_ok=True)
        
        try:
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                carts = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            carts = {}
        
        # Actualiza solo el carrito del usuario
        carts[str(cart.user_id)] = cart.to_dict()
        
        # Vuelve a escribir el archivo COMPLETO
        # Usamos la variable global CARTS_FILE
        with open(CARTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(carts, f, indent=4, ensure_ascii=False)

    def remove_cart(self, user_id):
        try:
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                carts = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            carts = {}
            
        if str(user_id) in carts:
            del carts[str(user_id)]
            
        # Usamos la variable global CARTS_FILE
        with open(CARTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(carts, f, indent=4, ensure_ascii=False)