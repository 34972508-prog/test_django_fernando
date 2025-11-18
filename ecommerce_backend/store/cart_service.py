# store/cart_service.py
import json
import os
# Importamos los "moldes" (modelos) de Carrito y Artículo.
from .models import Cart, CartItem

# --- Configuración de rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Esta es la ruta a NUESTRA "base de datos" de carritos.
# Guardará TODOS los carritos de TODOS los usuarios.
CARTS_FILE = os.path.join(BASE_DIR, 'data', 'carts.json') 

class CartService:
    
    # El constructor.
    def __init__(self):
        # Al iniciar el servicio, nos aseguramos de que el archivo
        # 'carts.json' exista en la carpeta 'data'.
        self._ensure_data_file_exists(CARTS_FILE) 

    # Función interna (privada) para crear el archivo si no existe.
    def _ensure_data_file_exists(self, file_path):
        # 1. Crea la carpeta 'data/' si no existe.
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # 2. Si el archivo 'carts.json' NO existe...
        if not os.path.exists(file_path):
            # ...lo creamos y escribimos un "{}" (un diccionario vacío)
            # para que sea un JSON válido desde el inicio.
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f) 

    # --- Métodos Públicos (APIs) ---

    def get_cart(self, user_id):
        """Busca el carrito de UN usuario específico por su ID."""
        
        self._ensure_data_file_exists(CARTS_FILE)
        
        try:
            # 1. Abrimos el archivo JSON que tiene TODOS los carritos.
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                # 'carts' será un diccionario: {"user_1": {...}, "user_2": {...}}
                carts = json.load(f)
        except json.JSONDecodeError:
            carts = {} # Si el archivo está corrupto, empezamos con un dict vacío.
            
        # 2. Buscamos el ID del usuario (como string) dentro de ese diccionario.
        if str(user_id) in carts:
            # ¡Lo encontramos! Tomamos los datos de su carrito.
            cart_data = carts[str(user_id)]
            
            # (Seguridad) Nos aseguramos de que la lista 'items' exista.
            if 'items' not in cart_data:
                cart_data['items'] = {}
                
            # Convertimos el diccionario de datos en un objeto "Cart" (usando el molde).
            return Cart.from_dict(cart_data)
        
        # 3. Si el usuario no existe en el JSON, creamos un carrito nuevo y vacío para él.
        return Cart(user_id=user_id)
    
    def get_all_carts(self):
        """
        Carga y devuelve TODOS los carritos del archivo JSON.
        (Esto es útil para un panel de Administrador).
        """
        self._ensure_data_file_exists(CARTS_FILE)
        
        try:
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                carts = json.load(f)
        except json.JSONDecodeError:
            carts = {}
        
        # Devuelve el diccionario completo {user_id: cart_data}
        return carts

    def save_cart(self, cart):
        """
        Actualiza (o añade) UN carrito específico en el archivo JSON.
        Este es el proceso "Leer -> Modificar -> Escribir".
        """
        os.makedirs(os.path.dirname(CARTS_FILE), exist_ok=True)
        
        try:
            # 1. LEEMOS el archivo COMPLETO con TODOS los carritos.
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                carts = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            carts = {} # Si no había archivo o estaba vacío.
        
        # 2. MODIFICAMOS solo la entrada de ESE usuario.
        #    Convertimos el objeto 'cart' (de models.py) a un diccionario simple.
        carts[str(cart.user_id)] = cart.to_dict()
        
        # 3. ESCRIBIMOS el archivo COMPLETO de nuevo en el disco.
        with open(CARTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(carts, f, indent=4, ensure_ascii=False)

    def remove_cart(self, user_id):
        """Elimina el carrito de UN usuario del archivo JSON."""
        try:
            # 1. Leemos TODOS los carritos.
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                carts = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            carts = {} # No hay nada que borrar.
            
        # 2. Si el usuario existe en el diccionario, lo borramos.
        if str(user_id) in carts:
            del carts[str(user_id)]
            
        # 3. Escribimos el archivo COMPLETO (ya sin ese usuario).
        with open(CARTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(carts, f, indent=4, ensure_ascii=False)