from abc import ABC, abstractmethod

# --- NUEVA CLASE BRANCH ---
class Branch:
    """Representa una sucursal o tienda física."""
    def __init__(self, branch_id, name, address, latitude, longitude):
        self._branch_id = branch_id
        self._name = name
        self._address = address
        self._latitude = latitude
        self._longitude = longitude

    @property
    def branch_id(self): return self._branch_id
    @property
    def name(self): return self._name
    @property
    def address(self): return self._address
    @property
    def latitude(self): return self._latitude
    @property
    def longitude(self): return self._longitude

    def to_dict(self):
        return {
            "id": self._branch_id,
            "name": self._name,
            "address": self._address,
            "latitude": self._latitude,
            "longitude": self._longitude,
        }
    
    def __str__(self):
        return self._name

# --- CLASE CATEGORY (Sin cambios) ---
class Category:
    def __init__(self, category_id, name):
        self._category_id = category_id
        self._name = name

    @property
    def category_id(self):
        return self._category_id

    @property
    def name(self):
        return self._name

    def to_dict(self):
        return {"id": self._category_id, "name": self._name}

    def __str__(self):
        return self._name

# --- CLASE BASE PRODUCT (Actualizada) ---
class Product(ABC):
    # Añadido 'branch_id' al constructor
    def __init__(self, product_id, title, description, price, stock, category_id, branch_id, image_url=None):
        self._product_id = product_id
        self._title = title
        self._description = description
        self.price = price
        self.stock = stock
        self._category_id = category_id
        self._branch_id = branch_id # <-- NUEVO
        self._image_url = image_url

    # Properties de Lectura
    @property
    def product_id(self): return self._product_id
    @property
    def title(self): return self._title
    @title.setter
    def title(self, value): self._title = value 
    @property
    def description(self): return self._description
    @description.setter
    def description(self, value): self._description = value
    @property
    def category_id(self): return self._category_id
    
    # --- NUEVO PROPERTY ---
    @property
    def branch_id(self): return self._branch_id
    @branch_id.setter
    def branch_id(self, value): self._branch_id = value
    # --- FIN NUEVO PROPERTY ---

    @property
    def image_url(self): return self._image_url
    @image_url.setter
    def image_url(self, value): self._image_url = value

    # Properties de Precio y Stock con validación
    @property
    def price(self): return self._price
    @price.setter
    def price(self, value):
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("El precio debe ser un número no negativo.")
        self._price = value

    @property
    def stock(self): return self._stock
    @stock.setter
    def stock(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("El stock debe ser un número entero no negativo.")
        self._stock = value

    @abstractmethod
    def get_invoice_description(self):
        pass

    def to_dict(self):
        # Añadido 'branch_id' al diccionario
        return {
            "id": self._product_id,
            "title": self._title,
            "description": self._description,
            "price": self._price,
            "stock": self._stock,
            "category_id": self._category_id,
            "branch_id": self._branch_id, # <-- NUEVO
            "image_url": self._image_url,
        }

# --- CLASE CAKEPRODUCT (Actualizada) ---
class CakeProduct(Product):
    """Representa un producto físico concreto (una torta) con un peso."""
    # Añadido 'branch_id' y pasado a super()
    def __init__(self, product_id, title, description, price, stock, category_id, branch_id, image_url=None, weight=None):
        super().__init__(product_id, title, description, price, stock, category_id, branch_id, image_url)
        self._weight = weight
        self.type = 'cake' 

    @property
    def weight(self): return self._weight
    @weight.setter
    def weight(self, value): self._weight = value

    def get_invoice_description(self):
        weight_info = f" (Peso: {self._weight}kg)" if self._weight else ""
        return f"Torta: {self._title}{weight_info}"

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": self.type, "weight": self._weight})
        return data


# --- CARRITO Y USUARIOS (Sin cambios) ---

class CartItem:
    def __init__(self, product_id, quantity=1):
        self.product_id = product_id
        self.quantity = quantity

class Cart:
    def __init__(self):
        self.items = {}  # product_id: CartItem
        
    def add_item(self, product_id, quantity=1):
        if product_id in self.items:
            self.items[product_id].quantity += quantity
        else:
            self.items[product_id] = CartItem(product_id, quantity)
    
    def remove_item(self, product_id):
        if product_id in self.items:
            del self.items[product_id]
    
    def get_total(self):
        from .product_service import ProductService
        total = 0
        service = ProductService()
        for item in self.items.values():
            product = service.get_product_by_id(item.product_id)
            if product:
                total += product['price'] * item.quantity
        return total

class BaseUser(ABC):
    def __init__(self, user_id, username, password):
        self._user_id = user_id
        self._username = username
        self._password = password 
    @property
    def user_id(self): return self._user_id
    @property
    def username(self): return self._username
    @property
    def password(self): return self._password
    @property
    @abstractmethod
    def role(self): pass
    def to_dict(self):
        return {
            "id": self._user_id,
            "username": self._username,
            "password": self._password,
            "role": self.role
        }

class ClientUser(BaseUser):
    @property
    def role(self): return "client"

class AdminUser(BaseUser):
    @property
    def role(self): return "admin"