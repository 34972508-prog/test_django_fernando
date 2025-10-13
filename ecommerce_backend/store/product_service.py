import json
#from models import Category, PhysicalProduct, DigitalProduct

# store/product_service.py

import os
# La importación de modelos ahora es relativa
from .models import Category, PhysicalProduct, DigitalProduct

#CATEGORIES_FILE = 'categories.json'
#PRODUCTS_FILE = 'products.json'
# --- RUTA DE ARCHIVOS ADAPTADA A DJANGO ---
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
            return []

    def _load_products(self):
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                products_list = []
                for item in data:
                    category = self.get_category_by_id(item['category_id'])
                    if not category: continue

                    if item['type'] == 'physical':
                        product = PhysicalProduct(item['id'], item['name'], item['price'], item['stock'], category, item['weight'])
                    elif item['type'] == 'digital':
                        product = DigitalProduct(item['id'], item['name'], item['price'], item['stock'], category, item['download_url'])
                    else:
                        continue
                    products_list.append(product)
                return products_list
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_products_to_file(self):
        products_as_dicts = []
        for p in self._products:
            d = p.to_dict()
            d['category_id'] = p.category.category_id
            del d['category']
            products_as_dicts.append(d)
        
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(products_as_dicts, f, indent=4, ensure_ascii=False)

    def get_category_by_id(self, category_id):
        return next((c for c in self._categories if c.category_id == category_id), None)

    def get_all_products(self, name_filter=None, category_id_filter=None):
        products_to_return = self._products
        if category_id_filter is not None:
            products_to_return = [p for p in products_to_return if p.category.category_id == category_id_filter]
        if name_filter:
            products_to_return = [p for p in products_to_return if name_filter.lower() in p.name.lower()]
        return [p.to_dict() for p in products_to_return]

    def get_product_by_id(self, product_id):
        product = next((p for p in self._products if p.product_id == product_id), None)
        return product.to_dict() if product else None

    def create_product(self, data):
        new_id = max([p.product_id for p in self._products], default=0) + 1
        category = self.get_category_by_id(data.get('category_id'))
        if not category: return None

        try:
            if data.get('type') == 'physical':
                product = PhysicalProduct(new_id, data['name'], data['price'], data['stock'], category, data['weight'])
            elif data.get('type') == 'digital':
                product = DigitalProduct(new_id, data['name'], data['price'], data['stock'], category, data['download_url'])
            else:
                return None
            
            self._products.append(product)
            self._save_products_to_file()
            return product.to_dict()
        except (KeyError, ValueError):
            return None

    def update_product(self, product_id, data):
        product_obj = next((p for p in self._products if p.product_id == product_id), None)
        if not product_obj: return None
        
        for key, value in data.items():
            if hasattr(product_obj, key):
                setattr(product_obj, key, value)
        
        self._save_products_to_file()
        return product_obj.to_dict()

    def delete_product(self, product_id):
        product_obj = next((p for p in self._products if p.product_id == product_id), None)
        if product_obj:
            self._products.remove(product_obj)
            self._save_products_to_file()
            return True
        return False