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
                    category_id = item['category_id']
                    if not self.get_category_by_id(category_id): continue

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

    def _save_products_to_file(self):
        products_as_dicts = [p.to_dict() for p in self._products]
        
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(products_as_dicts, f, indent=4, ensure_ascii=False)

    def get_category_by_id(self, category_id):
        return next((c for c in self._categories if c.category_id == category_id), None)

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
        if not self.get_category_by_id(category_id): return None
        
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
            product = CakeProduct(*common_args, weight=data['weight'])
            
            self._products.append(product)
            self._save_products_to_file()
            return product.to_dict()
        except (KeyError, ValueError):
            # Captura si falta 'weight' o si falla la validación (price/stock)
            return None

    def update_product(self, product_id, data):
        product_obj = next((p for p in self._products if p.product_id == product_id), None)
        if not product_obj: return None
        
        try:
            for key, value in data.items():
                if hasattr(product_obj, key):
                    setattr(product_obj, key, value)
                elif key == 'category_id' and self.get_category_by_id(value):
                    setattr(product_obj, '_category_id', value)
        
            self._save_products_to_file()
            return product_obj.to_dict()
        except ValueError:
            return None

    def delete_product(self, product_id):
        product_obj = next((p for p in self._products if p.product_id == product_id), None)
        if product_obj:
            self._products.remove(product_obj)
            self._save_products_to_file()
            return True
        return False