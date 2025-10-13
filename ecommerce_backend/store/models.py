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

class Product(ABC):
    def __init__(self, product_id, name, price, stock, category):
        self._product_id = product_id
        self._name = name
        self.price = price
        self.stock = stock
        self._category = category

    @property
    def product_id(self):
        return self._product_id

    @property
    def name(self):
        return self._name

    @property
    def category(self):
        return self._category

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

    @abstractmethod
    def get_invoice_description(self):
        pass

    def to_dict(self):
        return {
            "id": self._product_id,
            "name": self._name,
            "price": self._price,
            "stock": self._stock,
            "category": self._category.name if self._category else None,
        }

class PhysicalProduct(Product):
    def __init__(self, product_id, name, price, stock, category, weight):
        super().__init__(product_id, name, price, stock, category)
        self._weight = weight

    def get_invoice_description(self):
        return f"Producto Físico: {self._name} (Peso: {self._weight}kg)"

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "physical", "weight": self._weight})
        return data

class DigitalProduct(Product):
    def __init__(self, product_id, name, price, stock, category, download_url):
        super().__init__(product_id, name, price, stock, category)
        self._download_url = download_url

    def get_invoice_description(self):
        return f"Producto Digital: {self._name}"

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "digital", "download_url": self._download_url})
        return data