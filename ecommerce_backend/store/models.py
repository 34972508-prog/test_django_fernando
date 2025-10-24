from abc import ABC, abstractmethod

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

# --- CLASE BASE ABSTRACTA (Sin cambios) ---
class Product(ABC):
    def __init__(self, product_id, title, description, price, stock, category_id, image_url=None):
        self._product_id = product_id
        self._title = title
        self._description = description
        self.price = price
        self.stock = stock
        self._category_id = category_id
        self._image_url = image_url

    # Properties de Lectura
    @property
    def product_id(self):
        return self._product_id

    @property
    def title(self):
        return self._title
    @title.setter
    def title(self, value):
        self._title = value 

    @property
    def description(self):
        return self._description
    @description.setter
    def description(self, value):
        self._description = value

    @property
    def category_id(self):
        return self._category_id

    @property
    def image_url(self):
        return self._image_url
    @image_url.setter
    def image_url(self, value):
        self._image_url = value

    # Properties de Precio y Stock con validación
    @property
    def price(self):
        return self._price
    @price.setter
    def price(self, value):
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("El precio debe ser un número no negativo.")
        self._price = value

    @property
    def stock(self):
        return self._stock
    @stock.setter
    def stock(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("El stock debe ser un número entero no negativo.")
        self._stock = value

    # Método Abstracto que debe implementar CakeProduct
    @abstractmethod
    def get_invoice_description(self):
        pass

    def to_dict(self):
        return {
            "id": self._product_id,
            "title": self._title,
            "description": self._description,
            "price": self._price,
            "stock": self._stock,
            "category_id": self._category_id,
            "image_url": self._image_url,
        }

# --- CLASE CONCRETA PARA TORTAS ---
class CakeProduct(Product):
    """Representa un producto físico concreto (una torta) con un peso."""
    def __init__(self, product_id, title, description, price, stock, category_id, image_url=None, weight=None):
        super().__init__(product_id, title, description, price, stock, category_id, image_url)
        self._weight = weight
        self.type = 'cake' # Identificador para la serialización

    @property
    def weight(self):
        return self._weight
    
    @weight.setter
    def weight(self, value):
        self._weight = value

    # Implementación requerida por Product (ABC)
    def get_invoice_description(self):
        weight_info = f" (Peso: {self._weight}kg)" if self._weight else ""
        return f"Torta: {self._title}{weight_info}"

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": self.type, "weight": self._weight})
        return data