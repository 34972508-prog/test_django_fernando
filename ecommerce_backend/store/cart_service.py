import json
import os
from .models import Cart, CartItem

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARTS_FILE = os.path.join(BASE_DIR, 'data', 'carts.json')

class CartService:
    def __init__(self):
        self._ensure_data_file_exists()

    def _ensure_data_file_exists(self):
        os.makedirs(os.path.dirname(self.carts_file), exist_ok=True)
        if not os.path.exists(self.carts_file):
            with open(self.carts_file, 'w') as f:
                json.dump({}, f)

    def get_cart(self, user_id):
        with open(self.carts_file, 'r') as f:
            carts = json.load(f)
            if str(user_id) in carts:
                return Cart.from_dict(carts[str(user_id)])
        return Cart(user_id=user_id)

    def save_cart(self, cart):
        with open(self.carts_file, 'r+') as f:
            carts = json.load(f)
            carts[str(cart.user_id)] = cart.to_dict()
            f.seek(0)
            json.dump(carts, f)
            f.truncate()

    def remove_cart(self, user_id):
        """Eliminar el carrito de un usuario"""
        with open(self.carts_file, 'r+') as f:
            carts = json.load(f)
            if str(user_id) in carts:
                del carts[str(user_id)]
            f.seek(0)
            json.dump(carts, f)
            f.truncate()