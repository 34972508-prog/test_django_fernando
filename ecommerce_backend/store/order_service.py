import json
import os
from datetime import datetime
from typing import List, Dict, Optional

# Ruta absoluta para asegurar que use la misma carpeta data
# Nota: Usamos dirname(dirname(...)) para "subir un nivel"
# desde /services/ a /store/ y luego entrar a /data/.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDERS_FILE = os.path.join(BASE_DIR, 'store', 'data', 'orders.json')


class OrderService:
    def __init__(self):
        # Al iniciar el servicio, asegura que 'orders.json' exista.
        print(f"DEBUG OrderService - Inicializando, archivo: {ORDERS_FILE}")
        self._ensure_data_file_exists()
    
    def _ensure_data_file_exists(self):
        """Función interna: Crea el JSON si no existe."""
        print(f"DEBUG OrderService - Asegurando que existe {ORDERS_FILE}")
        os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
        if not os.path.exists(ORDERS_FILE):
            print("DEBUG OrderService - Creando archivo orders.json nuevo")
            # El archivo de órdenes necesita una estructura inicial:
            # una lista vacía de 'orders' y un contador 'next_order_id'.
            initial_data = {
                "orders": [],
                "next_order_id": 1001 # Empezamos las órdenes desde el ID 1001
            }
            with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=4, ensure_ascii=False)
        else:
            print("DEBUG OrderService - Archivo orders.json ya existe")
    
    # --- Funciones de Lectura/Escritura (Privadas) ---
    
    def _read_data(self):
        """Función interna: Lee el archivo JSON completo."""
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"DEBUG OrderService - Datos leídos: {len(data.get('orders', []))} órdenes")
                return data
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"DEBUG OrderService - Error leyendo archivo: {e}")
            # Si falla, devuelve la estructura por defecto.
            return {"orders": [], "next_order_id": 1001}
    
    def _write_data(self, data):
        """Función interna: Escribe el archivo JSON completo."""
        try:
            with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"DEBUG OrderService - Datos escritos exitosamente")
        except Exception as e:
            print(f"DEBUG OrderService - Error escribiendo datos: {e}")
            raise
    
    # --- Métodos Públicos (APIs del Servicio) ---
    
    def create_order(self, user_id: int, cart_data: Dict, user_data: Dict = None) -> Dict:
        """
        Toma los datos de un carrito y los convierte en una Orden permanente.
        """
        print(f"DEBUG OrderService - Creando orden para user_id: {user_id}")
        print(f"DEBUG OrderService - Cart data: {cart_data}")

        # 1. Leemos la base de datos actual de órdenes.
        data = self._read_data()

        # 2. "Enriquecemos" los items del carrito.
        # El carrito solo guarda (product_id, quantity).
        # La orden debe guardar (product_title, unit_price, total_price).
        enriched_items = []
        total_amount = 0
        print(f"DEBUG OrderService - Procesando {len(cart_data.get('items', {}))} items del carrito")

        for item_id, item in cart_data.get('items', {}).items():
            # ¡Importante! Usamos OTRO servicio (ProductService)
            # para obtener los detalles (precio, título) del producto.
            from .product_service import ProductService
            product_service = ProductService()
            product = product_service.get_product_by_id(item['product_id'])
            
            if product:
                # Calculamos el total de esta línea
                item_total = product['price'] * item['quantity']
                # Creamos el diccionario "enriquecido"
                enriched_item = {
                    "product_id": item['product_id'],
                    "product_title": product['title'],
                    "quantity": item['quantity'],
                    "unit_price": product['price'],
                    "total_price": item_total
                }
                enriched_items.append(enriched_item)
                # Sumamos al total general de la orden
                total_amount += item_total
                print(f"DEBUG OrderService - Producto {product['title']} x {item['quantity']} = {item_total}")
            else:
                print(f"DEBUG OrderService - Producto ID {item['product_id']} no encontrado")
        
         # 3. Creamos el objeto de la nueva orden
        new_order = {
            "id": data['next_order_id'], # Usamos el contador
            "user_id": user_id,
            "customer_info": user_data, # Datos del cliente (ej: dirección, email)
            "items": enriched_items,    # La lista de items enriquecidos
            "total_amount": total_amount,
            "status": "completed", # Estado inicial (simplificado)
            "branch_id": self._get_branch_from_cart(cart_data), # Asignamos la sucursal
            "order_type": "pickup",
            "created_at": datetime.now().isoformat(), # Fecha/Hora actual
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"DEBUG OrderService - Nueva orden: ID {new_order['id']}, Total: {total_amount}")
        
        # 4. Guardamos la orden en la base de datos
        data['orders'].append(new_order)
        data['next_order_id'] += 1 # Incrementamos el contador para la próxima orden
        
        self._write_data(data)
        print(f"DEBUG OrderService - Orden guardada exitosamente")
        
        return new_order
        

    
    def _get_branch_from_cart(self, cart_data: Dict) -> int:
        """Función interna: Determina a qué sucursal pertenece la orden."""
        # Lógica simplificada: asumimos que todos los productos del carrito
        # pertenecen a la misma sucursal.
        from .product_service import ProductService
        product_service = ProductService()
        
        # Buscamos el primer producto del carrito
        for item_id, item in cart_data.get('items', {}).items():
            product = product_service.get_product_by_id(item['product_id'])
            if product:
                # Devolvemos la sucursal de ese producto.
                return product.get('branch_id', 1)
        return 1 # Si el carrito está vacío, devolvemos '1' (default)
    
    # --- Métodos de Búsqueda ---
    
    def get_orders_by_user(self, user_id: int) -> List[Dict]:
        """Obtiene el historial de órdenes de un usuario."""
        data = self._read_data()
        # Filtra la lista de órdenes buscando el user_id
        return [order for order in data['orders'] if order['user_id'] == user_id]
    
    def get_all_orders(self) -> List[Dict]:
        """Obtiene TODAS las órdenes (para el admin)."""
        data = self._read_data()
        return data['orders']
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """Busca una orden específica por su ID."""
        data = self._read_data()
        for order in data['orders']:
            if order['id'] == order_id:
                return order
        return None
    
    def update_order_status(self, order_id: int, status: str) -> Optional[Dict]:
        """Permite al admin cambiar el estado de una orden (ej: 'preparando')."""
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled']
        
        if status not in valid_statuses:
            return None # Estado no válido
        
        data = self._read_data()
        for order in data['orders']:
            if order['id'] == order_id:
                # 1. Actualiza el estado
                order['status'] = status
                # 2. Actualiza la fecha de modificación
                order['updated_at'] = datetime.now().isoformat()
                # 3. Guarda los cambios en el JSON
                self._write_data(data)
                return order
        
        return None # Orden no encontrada