import json
import os
# Importamos los "moldes" que este servicio necesita
from .models import Category, CakeProduct 

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Este servicio maneja DOS archivos JSON
CATEGORIES_FILE = os.path.join(BASE_DIR, 'data', 'categories.json')
PRODUCTS_FILE = os.path.join(BASE_DIR, 'data', 'products.json')


class ProductService:
    def __init__(self):
        # 1. Carga las categorías PRIMERO (son una dependencia)
        self._categories = self._load_categories()
        # 2. Carga los productos (y los valida contra las categorías cargadas)
        self._products = self._load_products()

    # --- Carga de Datos (Privado) ---

    def _load_categories(self):
        """Carga 'categories.json' en una lista de objetos Category."""
        try:
            with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convierte la lista de dicts en lista de Objetos
                return [Category(c['id'], c['name']) for c in data]
        except (FileNotFoundError, json.JSONDecodeError):
            # Si falla, crea la carpeta y devuelve lista vacía
            os.makedirs(os.path.dirname(CATEGORIES_FILE), exist_ok=True)
            return []

    def _load_products(self):
        """Carga 'products.json' en una lista de objetos CakeProduct."""
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                products_list = []
                for item in data:
                    category_id = item.get('category_id') 
                    
                    # --- Validación de Dependencia ---
                    # Verificamos que la categoría del producto (category_id)
                    # realmente exista en nuestra lista (self._categories).
                    if not category_id or not any(c.category_id == category_id for c in self._categories):
                        print(f"Advertencia: Producto {item['id']} omitido. Categoría {category_id} no válida.")
                        continue # Ignoramos este producto y pasamos al siguiente

                    # Preparamos los argumentos para el constructor de Product/CakeProduct
                    common_args = (
                        item['id'],
                        item['title'],
                        item['description'],
                        item['price'],
                        item['stock'],
                        category_id,
                        item.get('branch_id'), # Añadimos la sucursal
                        item.get('image_url')
                    )

                    # Creamos el objeto (asumimos que todos son CakeProduct)
                    product = CakeProduct(*common_args, weight=item.get('weight'))
                    products_list.append(product)
                        
                return products_list
        except (FileNotFoundError, json.JSONDecodeError):
            os.makedirs(os.path.dirname(PRODUCTS_FILE), exist_ok=True)
            return []

    # --- Guardado de Datos (Privado) ---

    def _save_products_to_file(self):
        """Guarda la lista de objetos _products en 'products.json'"""
        # Llama a .to_dict() en cada objeto antes de guardar
        products_as_dicts = [p.to_dict() for p in self._products]
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(products_as_dicts, f, indent=4, ensure_ascii=False)

    def _save_categories_to_file(self):
        """Guarda la lista de objetos _categories en 'categories.json'"""
        categories_as_dicts = [c.to_dict() for c in self._categories]
        with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(categories_as_dicts, f, indent=4, ensure_ascii=False)

    # --- Métodos de Categorías (CRUD) ---

    def get_category_by_id(self, category_id):
        """Busca una categoría por ID (devuelve un dict)"""
        category = next((c for c in self._categories if c.category_id == category_id), None)
        return category.to_dict() if category else None

    def get_all_categories(self):
        """Devuelve todas las categorías (lista de dicts)"""
        return [c.to_dict() for c in self._categories]
  
    def create_category(self, data):
        """Crea una nueva categoría."""
        try:
            name = data.get('name')
            if not name: return None # Nombre es obligatorio
            # 1. Calcula el nuevo ID
            new_id = max([c.category_id for c in self._categories], default=0) + 1
            # 2. Crea el objeto
            new_category = Category(category_id=new_id, name=name)
            # 3. Añade a la lista en memoria
            self._categories.append(new_category)
            # 4. Guarda en el JSON
            self._save_categories_to_file()
            return new_category.to_dict()
        except Exception as e:
            print(f"Error al crear categoría: {e}")
            return None
        
    def update_category(self, category_id, data):
        """Actualiza el nombre de una categoría."""
        try:
            # 1. Busca el OBJETO en la lista
            category_in_list = next((c for c in self._categories if c.category_id == category_id), None)
            if not category_in_list:
                print(f"Error: Categoría {category_id} no encontrada")
                return None
            
            # 2. Actualiza el nombre (los objetos se modifican "por referencia")
            new_name = data.get('name')
            if new_name:
                category_in_list._name = new_name 
                # 3. Guarda la lista actualizada en el JSON
                self._save_categories_to_file()
                return category_in_list.to_dict()
            return None
        except Exception as e:
            print(f"Error al actualizar categoría: {e}")
            return None

    # --- Métodos de Productos (CRUD) ---

    def get_all_products(self, title_filter=None, category_id_filter=None):
        """
        Devuelve todos los productos (lista de dicts),
        con filtros opcionales por título o categoría.
        """
        products_to_return = self._products # Empezamos con todos
        
        # Aplicamos filtro de categoría
        if category_id_filter is not None:
            products_to_return = [p for p in products_to_return if p.category_id == category_id_filter]
        
        # Aplicamos filtro de título
        if title_filter:
            products_to_return = [p for p in products_to_return if title_filter.lower() in p.title.lower()]
        
        # Devolvemos la lista filtrada (convertida a dicts)
        return [p.to_dict() for p in products_to_return]

    def get_product_by_id(self, product_id):
        """Busca un producto por ID (devuelve un dict)"""
        product = next((p for p in self._products if p.product_id == product_id), None)
        return product.to_dict() if product else None

    def create_product(self, data):
        """Crea un nuevo producto (CakeProduct)."""
        
        new_id = max([p.product_id for p in self._products], default=0) + 1
        category_id = data.get('category_id')
        branch_id = data.get('branch_id') # <-- NUEVO
        
        # Validación: La categoría debe existir
        if not category_id or not any(c.category_id == category_id for c in self._categories):
            print(f"Error: Intento de crear producto con categoría inválida {category_id}")
            return None 
        
        # (Opcional) Faltaría verificar si la sucursal (branch_id) existe
        # usando el BranchService.
        
        # Argumentos para el constructor
        common_args = (
            new_id,
            data.get('title'),
            data.get('description'),
            data.get('price'),
            data.get('stock'),
            category_id,
            branch_id, # <-- NUEVO
            data.get('image_url')
        )
        try:
            # 1. Creamos el objeto
            product = CakeProduct(*common_args, weight=data.get('weight'))
            # 2. Añadimos a la lista en memoria
            self._products.append(product)
            # 3. Guardamos en el JSON
            self._save_products_to_file()
            return product.to_dict()
        except (KeyError, ValueError, TypeError) as e:
            # Captura errores si faltan datos (KeyError)
            # o si el precio/stock no es un número (ValueError)
            print(f"Error en create_product: {e}")
            return None

    def update_product(self, product_id, data):
        """Actualiza los datos de un producto existente."""
        
        # 1. Buscamos el OBJETO en la lista
        product_obj = next((p for p in self._products if p.product_id == product_id), None)
        if not product_obj: 
            return None # No se encontró
        
        # 2. Actualizamos campo por campo, usando los "setters" del modelo
        try:
            if 'title' in data and data['title']: product_obj.title = data['title']
            if 'description' in data: product_obj.description = data['description']
            if 'price' in data and data['price'] is not None: product_obj.price = float(data['price'])
            if 'stock' in data and data['stock'] is not None: product_obj.stock = int(data['stock'])
            if 'image_url' in data: product_obj.image_url = data['image_url']
            if 'weight' in data and data['weight'] is not None and hasattr(product_obj, 'weight'): product_obj.weight = float(data['weight'])
            
            # --- NUEVO: Actualizar Categoría y Sucursal ---
            if 'category_id' in data and data['category_id'] is not None:
                category_id = int(data['category_id'])
                # Verificamos que la nueva categoría exista
                if any(c.category_id == category_id for c in self._categories):
                    product_obj._category_id = category_id
            
            if 'branch_id' in data and data['branch_id'] is not None:
                product_obj.branch_id = int(data['branch_id'])
            # --- FIN NUEVO ---
                
            # 3. Guardamos la lista actualizada en el JSON
            self._save_products_to_file()
            return product_obj.to_dict()
            
        except ValueError as e:
            # Error de validación (ej: precio negativo)
            print(f"Error de validación en update_product: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado en update_product: {e}")
            return None

    def delete_product(self, product_id):
        """Elimina un producto por ID."""
        # 1. Busca el OBJETO
        product_obj = next((p for p in self._products if p.product_id == product_id), None)
        if product_obj:
            # 2. Lo quita de la lista en memoria
            self._products.remove(product_obj)
            # 3. Guarda la lista actualizada en el JSON
            self._save_products_to_file()
            return True
        return False
    
    def delete_category(self, category_id):
        """Elimina una categoría, SOLO si no está en uso."""
        
        # 1. Verificación de integridad: ¿Algún producto usa esta categoría?
        is_in_use = any(p.category_id == category_id for p in self._products)
        if is_in_use:
            print(f"Error: Categoría {category_id} está en uso por un producto.")
            return False # No se puede borrar
        
        # 2. Si no está en uso, la buscamos
        category_obj = next((c for c in self._categories if c.category_id == category_id), None)
        if category_obj:
            # 3. La quitamos de la lista y guardamos
            self._categories.remove(category_obj)
            self._save_categories_to_file()
            return True
        return False