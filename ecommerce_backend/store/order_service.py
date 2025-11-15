# store/order_service.py
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORDERS_FILE = os.path.join(BASE_DIR, 'data', 'orders.json')

class OrderService:

    def __init__(self):
        self._ensure_data_file_exists()

    def _ensure_data_file_exists(self):
        os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
        if not os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f) # Las órdenes se guardan como una LISTA

    def _load_orders(self):
        """Carga la LISTA de órdenes desde el JSON."""
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_orders(self, orders_list):
        """Guarda la LISTA de órdenes en el JSON."""
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders_list, f, indent=4, ensure_ascii=False)

    def _get_next_order_id(self, orders_list):
        """Genera un nuevo ID de orden."""
        if not orders_list:
            return 1
        return max(order.get('order_id', 0) for order in orders_list) + 1

    def get_all_orders(self):
        """Devuelve todas las órdenes, ordenadas de más nueva a más vieja."""
        orders = self._load_orders()
        return sorted(orders, key=lambda x: x.get('order_date'), reverse=True)

    def create_order(self, user_id, branch_id, items_list, total_amount):
        """
        Crea un registro de orden permanente.
        'items_list' es la lista de {'product': product_dict, 'quantity': int}
        """
        orders = self._load_orders()
        
        # 1. Formatear los productos para la orden
        order_items = []
        for item in items_list:
            product = item['product']
            quantity = item['quantity']
            order_items.append({
                'product_id': product['id'],
                'product_title': product['title'],
                'quantity': quantity,
                'price_at_purchase': product['price'] # Guarda el precio al momento de la compra
            })

        # 2. Crear el objeto de la nueva orden
        new_order = {
            'order_id': self._get_next_order_id(orders),
            'user_id': user_id,
            'branch_id': branch_id,
            'order_date': datetime.now().isoformat(), # Guarda la fecha y hora
            'total_amount': total_amount,
            'items': order_items
        }

        # 3. Guardar en el historial
        orders.append(new_order)
        self._save_orders(orders)
        
        return new_order