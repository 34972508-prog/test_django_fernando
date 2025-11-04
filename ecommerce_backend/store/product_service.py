import json
import os
# Solo importamos Category y la clase específica para tortas
from .models import Category, CakeProduct 

# Configuración de rutas (ajusta 'data' según la estructura de tu proyecto)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_FILE = os.path.join(BASE_DIR, 'data', 'categories.json')
PRODUCTS_FILE = os.path.join(BASE_DIR, 'data', 'products.json')


class ProductService:
    def __init__(self):
        self._categories = self._load_categories()
        self._products = self._load_products()

    def _load_categories(self):
        try:
            with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Category(c['id'], c['name']) for c in data]
        except (FileNotFoundError, json.JSONDecodeError):
            os.makedirs(os.path.dirname(CATEGORIES_FILE), exist_ok=True)
            return []

    def _load_products(self):
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                products_list = []
                for item in data:
                    # Corrección: Usar self.get_category_by_id (el método de instancia)
                    category_id = item['category_id']
                    # Asegurarse de que la categoría exista antes de cargar el producto
                    if not next((c for c in self._categories if c.category_id == category_id), None):
                        continue # Omite este producto si su categoría no está en self._categories

                    # Argumentos comunes (basados en el constructor de Product)
                    common_args = (
                        item['id'],
                        item['title'],
                        item['description'],
                        item['price'],
                        item['stock'],
                        category_id,
                        item.get('image_url')
                    )

                    # Instanciación directa de CakeProduct
                    product = CakeProduct(*common_args, weight=item.get('weight'))
                    products_list.append(product)
                        
                return products_list
        except (FileNotFoundError, json.JSONDecodeError):
            os.makedirs(os.path.dirname(PRODUCTS_FILE), exist_ok=True)
            return []

    #servicio actualiza json
    def _save_products_to_file(self):
        products_as_dicts = [p.to_dict() for p in self._products]
        
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(products_as_dicts, f, indent=4, ensure_ascii=False)

    # --- Métodos de Categorías ---

    def _save_categories_to_file(self):
        """Guarda la lista actual de categorías en el archivo JSON."""
        categories_as_dicts = [c.to_dict() for c in self._categories]
        
        with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(categories_as_dicts, f, indent=4, ensure_ascii=False)

    def get_category_by_id(self, category_id):
        """Busca una categoría por ID y devuelve su diccionario."""
        category = next((c for c in self._categories if c.category_id == category_id), None)
        return category.to_dict() if category else None # Devuelve dict

    def get_all_categories(self):
        """Devuelve la lista de diccionarios de categorías."""
        return [c.to_dict() for c in self._categories]
  
    def create_category(self, data):
        """Crea un nuevo objeto Categoría y lo guarda en el JSON."""
        try:
            name = data.get('name')
            if not name:
                return None # Requiere un nombre

            # Calcula el nuevo ID
            new_id = max([c.category_id for c in self._categories], default=0) + 1
            
            new_category = Category(category_id=new_id, name=name)
            
            self._categories.append(new_category)
            self._save_categories_to_file()
            
            return new_category.to_dict()
        except Exception as e:
            print(f"Error al crear categoría: {e}")
            return None
        
    def update_category(self, category_id, data):
        """Actualiza el nombre de una categoría existente."""
        try:
            # Busca el objeto real en la lista self._categories
            category_in_list = next((c for c in self._categories if c.category_id == category_id), None)
            
            if not category_in_list:
                print(f"Error: Categoría {category_id} no encontrada")
                return None

            new_name = data.get('name')
            if new_name:
                # Actualiza el atributo privado del objeto
                category_in_list._name = new_name 
                self._save_categories_to_file()
                return category_in_list.to_dict()
            
            return None
        except Exception as e:
            print(f"Error al actualizar categoría: {e}")
            return None

    # --- Métodos de Productos ---

    def get_all_products(self, title_filter=None, category_id_filter=None):
        products_to_return = self._products
        
        if category_id_filter is not None:
            products_to_return = [p for p in products_to_return if p.category_id == category_id_filter]
            
        if title_filter:
            products_to_return = [p for p in products_to_return if title_filter.lower() in p.title.lower()]
            
        return [p.to_dict() for p in products_to_return]

    def get_product_by_id(self, product_id):
        product = next((p for p in self._products if p.product_id == product_id), None)
        return product.to_dict() if product else None

    def create_product(self, data):
        new_id = max([p.product_id for p in self._products], default=0) + 1
        category_id = data.get('category_id')
        
        # Verifica que la categoría exista usando la lista de objetos
        if not next((c for c in self._categories if c.category_id == category_id), None):
            return None
        
        common_args = (
            new_id,
            data.get('title'),
            data.get('description'),
            data.get('price'),
            data.get('stock'),
            category_id,
            data.get('image_url')
        )

        try:
            # Instanciación directa de CakeProduct (asume que 'weight' está en 'data')
            product = CakeProduct(*common_args, weight=data.get('weight')) # Usar .get para evitar KeyError
            
            self._products.append(product)
            self._save_products_to_file()
            return product.to_dict()
        except (KeyError, ValueError, TypeError) as e:
            # Captura si falta 'weight' o si falla la validación (price/stock)
            print(f"Error en create_product: {e}")
            return None


    def update_product(self, product_id, data):
        #print(f"🔧 DEBUG update_product: ID={product_id}, data={data}")
        
        product_obj = next((p for p in self._products if p.product_id == product_id), None)
        if not product_obj: 
            #print(f"❌ Producto con ID {product_id} no encontrado")
            return None
        
        try:
            # Campos permitidos y cómo actualizarlos
            updates_applied = {}
            
            # 1. Actualizar título
            if 'title' in data and data['title']:
                product_obj.title = data['title']
                updates_applied['title'] = data['title']
            
            # 2. Actualizar descripción
            if 'description' in data:
                product_obj.description = data['description']
                updates_applied['description'] = data['description']
            
            # 3. Actualizar precio
            if 'price' in data and data['price'] is not None:
                product_obj.price = float(data['price'])
                updates_applied['price'] = data['price']
            
            # 4. Actualizar stock
            if 'stock' in data and data['stock'] is not None:
                product_obj.stock = int(data['stock'])
                updates_applied['stock'] = data['stock']
            
            # 5. Actualizar categoría (atributo interno)
            if 'category_id' in data and data['category_id'] is not None:
                category_id = int(data['category_id'])
                # Verifica que la categoría exista usando la lista de objetos
                if next((c for c in self._categories if c.category_id == category_id), None):
                    product_obj._category_id = category_id
                    updates_applied['category_id'] = category_id
                #else:
                    #print(f"⚠️  Categoría ID {category_id} no existe, se mantiene la actual")
            
            # 6. Actualizar imagen
            if 'image_url' in data:
                product_obj.image_url = data['image_url']
                updates_applied['image_url'] = data['image_url']
            
            # 7. Actualizar peso (solo para CakeProduct)
            if 'weight' in data and data['weight'] is not None and hasattr(product_obj, 'weight'):
                product_obj.weight = float(data['weight'])
                updates_applied['weight'] = data['weight']
            
            #print(f"✅ Updates aplicados: {updates_applied}")
            
            # Guardar cambios
            self._save_products_to_file()
            
            # Devolver el producto actualizado
            updated_product = product_obj.to_dict()
            #print(f"✅ Producto actualizado: {updated_product}")
            
            return updated_product
            
        except ValueError as e:
            #print(f"❌ Error de validación en update_product: {e}")
            return None
        except Exception as e:
            #print(f"❌ Error inesperado en update_product: {e}")
            import traceback
            traceback.print_exc()
            return None

    def delete_product(self, product_id):
        #print(f"🔍 DELETE SERVICE llamado para producto {product_id}")
        product_obj = next((p for p in self._products if p.product_id == product_id), None)
        if product_obj:
            self._products.remove(product_obj)
            self._save_products_to_file()
            return True
        return False
    

    # --- MÉTODO NUEVO ---
    def delete_category(self, category_id):
        """Elimina una categoría si no está en uso por ningún producto."""
        
        # 1. Verificar si la categoría está en uso
        # Usamos self._products (la lista de objetos)
        is_in_use = any(p.category_id == category_id for p in self._products)
        if is_in_use:
            print(f"Error: Categoría {category_id} está en uso y no puede ser eliminada.")
            return False # Indicar fallo (en uso)

        # 2. Si no está en uso, proceder a eliminar
        # Usamos self._categories (la lista de objetos)
        category_obj = next((c for c in self._categories if c.category_id == category_id), None)
        
        if category_obj:
            self._categories.remove(category_obj)
            self._save_categories_to_file()
            return True # Éxito
        
        return False # No encontrada