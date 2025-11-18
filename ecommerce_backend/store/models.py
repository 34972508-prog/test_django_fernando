from abc import ABC, abstractmethod # (ABC = Abstract Base Class)

# --- NUEVA CLASE BRANCH ---
class Branch:
    """
    Representa el "molde" (modelo) para una Sucursal física.
    Define qué datos debe tener cada sucursal.
    """
    def __init__(self, branch_id, name, address, latitude, longitude, is_open , opening_hours, phone):
        # Usamos guion bajo (_) para marcar estos datos como "internos" o "protegidos".
        self._branch_id = branch_id
        self._name = name
        self._address = address
        self._latitude = latitude
        self._longitude = longitude
        self._is_open = is_open
        self._opening_hours = opening_hours
        self._phone = phone

    # Los "@property" nos permiten acceder a los datos internos
    # como si fueran variables públicas (ej: branch.name),
    # pero nos da control (en este caso, solo lectura).
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
    @property
    def is_open(self): return self._is_open
    @property
    def opening_hours(self): return self._opening_hours
    @property
    def phone(self): return self._phone

    def to_dict(self):
        """
        Convierte el Objeto (Branch) en un diccionario simple.
        Esto es vital para poder convertirlo a JSON fácilmente.
        """
        return {
            "id": self._branch_id,
            "name": self._name,
            "address": self._address,
            "latitude": self._latitude,
            "longitude": self._longitude,
            "is_open": self._is_open,
            "opening_hours": self._opening_hours,
            "phone": self._phone
        }
    
    def __str__(self):
        # Define qué mostrar si hacemos print(branch_object)
        return self._name

# --- CLASE CATEGORY (Molde para Categorías) ---
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

# "ABC" (Abstract Base Class) significa que esta clase "Product"
# es un molde GENERAL. No se puede crear un "Producto" genérico,
# solo se pueden crear sus hijos (ej: CakeProduct).
class Product(ABC):
    
    # El constructor (init) ahora incluye 'branch_id'
    def __init__(self, product_id, title, description, price, stock, category_id, branch_id, image_url=None):
        self._product_id = product_id
        self._title = title
        self._description = description
        self.price = price  # (Usará el @price.setter de abajo)
        self.stock = stock  # (Usará el @stock.setter de abajo)
        self._category_id = category_id
        self._branch_id = branch_id # <-- NUEVO: ID de la sucursal a la que pertenece
        self._image_url = image_url

    # --- Properties (Getters/Setters) ---

    # Properties de solo lectura (Getters)
    @property
    def product_id(self): return self._product_id
    
    # Properties con Getter y Setter (Lectura/Escritura)
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
    @branch_id.setter # (Permite cambiarlo después: product.branch_id = 5)
    def branch_id(self, value): self._branch_id = value
    # --- FIN NUEVO PROPERTY ---

    @property
    def image_url(self): return self._image_url
    @image_url.setter
    def image_url(self, value): self._image_url = value

    # Properties con validación (Setters)
    # Estos 'setters' protegen nuestros datos.
    @property
    def price(self): return self._price
    @price.setter
    def price(self, value):
        # No permite guardar precios negativos o que no sean números.
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("El precio debe ser un número no negativo.")
        self._price = value

    @property
    def stock(self): return self._stock
    @stock.setter
    def stock(self, value):
        # No permite stock negativo o decimal.
        if not isinstance(value, int) or value < 0:
            raise ValueError("El stock debe ser un número entero no negativo.")
        self._stock = value

    @abstractmethod
    def get_invoice_description(self):
        # "abstractmethod" OBLIGA a las clases hijas (CakeProduct)
        # a implementar esta función.
        pass

    def to_dict(self):
        # El diccionario base que tendrán todos los productos.
        # Añadido 'branch_id'
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

# CakeProduct "hereda" todo de Product (es un "hijo").
class CakeProduct(Product):
    """Representa un producto físico concreto (una torta) con un peso."""
    
    # Recibe 'branch_id' y se lo pasa al "padre" (super)
    def __init__(self, product_id, title, description, price, stock, category_id, branch_id, image_url=None, weight=None):
        # 1. Llama al constructor del "padre" (Product)
        super().__init__(product_id, title, description, price, stock, category_id, branch_id, image_url)
        # 2. Añade las propiedades específicas de "CakeProduct"
        self._weight = weight
        self.type = 'cake' # Para identificarlo en el JSON

    @property
    def weight(self): return self._weight
    @weight.setter
    def weight(self, value): self._weight = value

    def get_invoice_description(self):
        # Implementación obligatoria del método abstracto
        weight_info = f" (Peso: {self._weight}kg)" if self._weight else ""
        return f"Torta: {self._title}{weight_info}"

    def to_dict(self):
        # 1. Obtiene el diccionario del "padre" (Product.to_dict())
        data = super().to_dict()
        # 2. Le añade los datos específicos de "CakeProduct"
        data.update({"type": self.type, "weight": self._weight})
        return data


# --- CARRITO Y USUARIOS ---

class CartItem:
    """Molde simple para un item DENTRO del carrito (solo ID y cantidad)"""
    def __init__(self, product_id, quantity=1):
        self.product_id = product_id
        self.quantity = quantity

class Cart:
    """Molde para el Carrito de compras."""
    def __init__(self, user_id=None):
        self.user_id = user_id
        # El carrito es un diccionario de CartItems
        # { 101: CartItem(101, 2), 102: CartItem(102, 1) }
        self.items = {}  
        
    def add_item(self, product_id, quantity=1):
        # Lógica para añadir o sumar cantidad si ya existe.
        product_id = int(product_id)
        if product_id in self.items:
            self.items[product_id].quantity += quantity
        else:
            self.items[product_id] = CartItem(product_id, quantity)
    
    def to_dict(self):
        # Convierte el objeto Cart (y sus CartItems) a un diccionario
        # listo para guardar en el JSON (ver cart_service.py)
        return {
            "user_id": self.user_id,
            "items": {str(k): {"product_id": v.product_id, "quantity": v.quantity} 
                     for k, v in self.items.items()}
        }
    
    def remove_item(self, product_id):
        # Lógica para quitar un item
        product_id = int(product_id)
        if product_id in self.items:
            del self.items[product_id]
    
    def get_total(self):
        # Calcula el total del carrito (usando el ProductService)
        # (Esto es una "dependencia" entre servicios)
        from .product_service import ProductService
        total = 0
        service = ProductService()
        for item in self.items.values():
            product = service.get_product_by_id(item.product_id)
            if product:
                total += product['price'] * item.quantity
        return total

    @classmethod
    def from_dict(cls, data):
        """Método 'de fábrica': Crea un objeto Cart desde un diccionario (del JSON)"""
        cart = cls(user_id=data.get('user_id'))
        # Reconstruye los objetos CartItem
        for product_id, item_data in data.get('items', {}).items():
            cart.items[int(product_id)] = CartItem(
                item_data['product_id'], 
                item_data['quantity']
            )
        return cart

# --- Clases de Usuario (Base, Cliente, Admin) ---

class BaseUser(ABC):
    """Molde abstracto (base) para todos los tipos de usuario."""
    def __init__(self, user_id, username, password, email=None, address=None):
        self._user_id = user_id
        self._username = username
        self._password = password # (En un proyecto real, esto estaría hasheado)
        self._email = email
        self._address = address

    # --- Properties (Getters) ---
    @property
    def user_id(self): return self._user_id
    @property
    def username(self): return self._username
    @property
    def password(self): return self._password
    @property
    def email(self): return self._email
    @property
    def address(self): return self._address
    
    @property
    @abstractmethod
    def role(self): 
        # Obliga a las clases hijas (Client, Admin) a definir un rol.
        pass
    
    def to_dict(self):
        # Diccionario base para todos los usuarios.
        return {
            "id": self._user_id,
            "username": self._username,
            "password": self._password, # (No enviar esto a un front-end real)
            "role": self.role, # Llama al @property 'role' (sea de Client o Admin)
            "email": self._email,
            "address": self._address
        }

class ClientUser(BaseUser):
    """Molde para un usuario Cliente."""
    
    def __init__(self, user_id, username, password, email=None, address=None):
        # Llama al constructor del padre (BaseUser) con todos los datos
        super().__init__(user_id, username, password, email, address) 

    @property
    def role(self): 
        # Implementación obligatoria
        return "client"

class AdminUser(BaseUser):
    """Molde para un usuario Administrador."""
    
    def __init__(self, user_id, username, password, email=None, address=None):
        # Llama al constructor del padre (BaseUser) con todos los datos
        super().__init__(user_id, username, password, email, address)
        
    @property
    def role(self): 
        # Implementación obligatoria
        return "admin"