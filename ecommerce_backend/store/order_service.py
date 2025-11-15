import json
import os
from datetime import datetime
from typing import List, Dict, Optional

# Ruta absoluta para asegurar que use la misma carpeta data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDERS_FILE = os.path.join(BASE_DIR, 'store', 'data', 'orders.json')


class OrderService:
    def __init__(self):
        print(f"DEBUG OrderService - Inicializando, archivo: {ORDERS_FILE}")
        self._ensure_data_file_exists()
    
    def _ensure_data_file_exists(self):
        """Asegura que el archivo orders.json exista con estructura inicial"""
        print(f"DEBUG OrderService - Asegurando que existe {ORDERS_FILE}")
        os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
        if not os.path.exists(ORDERS_FILE):
            print("DEBUG OrderService - Creando archivo orders.json nuevo")
            initial_data = {
                "orders": [],
                "next_order_id": 1001
            }
            with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=4, ensure_ascii=False)
        else:
            print("DEBUG OrderService - Archivo orders.json ya existe")
    
    def _read_data(self):
        """Lee los datos del archivo orders.json"""
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"DEBUG OrderService - Datos leídos: {len(data.get('orders', []))} órdenes")
                return data
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"DEBUG OrderService - Error leyendo archivo: {e}")
            return {"orders": [], "next_order_id": 1001}
    
    def _write_data(self, data):
        """Escribe datos en el archivo orders.json"""
        try:
            with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"DEBUG OrderService - Datos escritos exitosamente")
        except Exception as e:
            print(f"DEBUG OrderService - Error escribiendo datos: {e}")
            raise
    
    def create_order(self, user_id: int, cart_data: Dict, user_data: Dict = None) -> Dict:
        """
        Crea una nueva orden a partir del carrito
        """
        print(f"DEBUG OrderService - Creando orden para user_id: {user_id}")
        print(f"DEBUG OrderService - Cart data: {cart_data}")

        data = self._read_data()

        # Enriquecer items con información completa del producto
        enriched_items = []
        total_amount = 0
        print(f"DEBUG OrderService - Procesando {len(cart_data.get('items', {}))} items del carrito")

        for item_id, item in cart_data.get('items', {}).items():
            from .product_service import ProductService
            product_service = ProductService()
            product = product_service.get_product_by_id(item['product_id'])
            
            if product:
                item_total = product['price'] * item['quantity']
                enriched_item = {
                    "product_id": item['product_id'],
                    "product_title": product['title'],
                    "quantity": item['quantity'],
                    "unit_price": product['price'],
                    "total_price": item_total
                }
                enriched_items.append(enriched_item)
                total_amount += item_total
                print(f"DEBUG OrderService - Producto {product['title']} x {item['quantity']} = {item_total}")
            else:
                print(f"DEBUG OrderService - Producto ID {item['product_id']} no encontrado")
        
         # Crear nueva orden
        new_order = {
            "id": data['next_order_id'],
            "user_id": user_id,
            "customer_info": user_data,
            "items": enriched_items,
            "total_amount": total_amount,
            "status": "completed",
            "branch_id": self._get_branch_from_cart(cart_data),
            "order_type": "pickup",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"DEBUG OrderService - Nueva orden: ID {new_order['id']}, Total: {total_amount}")
        
        data['orders'].append(new_order)
        data['next_order_id'] += 1
        
        self._write_data(data)
        print(f"DEBUG OrderService - Orden guardada exitosamente")
        
        return new_order
        

    
    def _get_branch_from_cart(self, cart_data: Dict) -> int:
        """Obtiene la sucursal del primer producto en el carrito"""
        from .product_service import ProductService
        product_service = ProductService()
        
        for item_id, item in cart_data.get('items', {}).items():
            product = product_service.get_product_by_id(item['product_id'])
            if product:
                return product.get('branch_id', 1)
        return 1
    
    def get_orders_by_user(self, user_id: int) -> List[Dict]:
        """Obtiene todas las órdenes de un usuario"""
        data = self._read_data()
        return [order for order in data['orders'] if order['user_id'] == user_id]
    
    def get_all_orders(self) -> List[Dict]:
        """Obtiene todas las órdenes"""
        data = self._read_data()
        return data['orders']
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """Obtiene una orden por ID"""
        data = self._read_data()
        for order in data['orders']:
            if order['id'] == order_id:
                return order
        return None
    
    def update_order_status(self, order_id: int, status: str) -> Optional[Dict]:
        """Actualiza el estado de una orden"""
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled']
        
        if status not in valid_statuses:
            return None
        
        data = self._read_data()
        for order in data['orders']:
            if order['id'] == order_id:
                order['status'] = status
                order['updated_at'] = datetime.now().isoformat()
                self._write_data(data)
                return order
        
        return None