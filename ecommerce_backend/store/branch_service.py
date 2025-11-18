# store/branch_service.py

# Este archivo será el "motor" o "controlador" de la lógica de negocio
# para todo lo relacionado con las Sucursales.

import json
import os
# Importamos el "molde" de Sucursal (el objeto Branch) desde models.py
from .models import Branch 

# --- Configuración de rutas ---
# Necesitamos saber dónde estamos parados para encontrar el JSON.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Definimos la ruta exacta de nuestro "mini-base de datos" JSON.
BRANCHES_FILE = os.path.join(BASE_DIR, 'data', 'sucursales.json')


# Esta clase agrupa toda la funcionalidad de las sucursales.
# Actúa como un intermediario entre los datos (el JSON) y el resto de la app.
class BranchService:
    
    # El "constructor": Se ejecuta automáticamente cuando creamos un BranchService.
    def __init__(self):
        # Apenas se crea el servicio, cargamos todas las sucursales desde el JSON
        # y las guardamos en la variable interna "_branches".
        self._branches = self._load_branches()

    # Función interna (privada) para leer el archivo JSON.
    def _load_branches(self):
        """Lee el JSON y lo convierte en una lista de objetos Branch."""
        
        # Intentamos leer el archivo.
        try:
            # Abrimos el archivo JSON en modo lectura ('r') y con codificación UTF-8.
            with open(BRANCHES_FILE, 'r', encoding='utf-8') as f:
                # 1. Cargamos el JSON y lo convertimos a una lista de diccionarios de Python.
                data = json.load(f)
                
                # 2. Convertimos esa lista de diccionarios en una lista de Objetos "Branch".
                #    Usamos el "molde" (la clase Branch) que importamos antes.
                return [
                    Branch(
                        branch_id=b['id'],
                        name=b['name'],
                        address=b['address'],
                        latitude=b['latitude'],
                        longitude=b['longitude'],
                        is_open=b['is_open'],
                        opening_hours=b['opening_hours'],
                        phone=b['phone']
                    ) for b in data
                ]
        
        # --- Manejo de Errores ---
        # Si algo falla al leer el archivo (ej: no existe, el JSON está mal escrito)...
        except Exception as e: 
            # ...imprimimos un mensaje de error muy claro en la consola.
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR GRAVE AL CARGAR SUCURSALES: {e}")
            print(f"La ruta del archivo que se intentó leer es:")
            print(BRANCHES_FILE)
            print("Por favor, verifica que el archivo exista y que el JSON sea válido.")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # Devolvemos una lista vacía para que la aplicación no se caiga.
            return [] 
        # --- Fin del Manejo de Errores ---


    # --- Métodos Públicos (APIs) ---

    def get_all_branches(self):
        """Función pública: Devuelve TODAS las sucursales."""
        # Convierte nuestra lista de objetos Branch a una lista de diccionarios simples.
        return [b.to_dict() for b in self._branches]

    def get_branch_by_id(self, branch_id):
        """Función pública: Busca y devuelve UNA sucursal por su ID."""
        
        # Buscamos en la lista interna la primera sucursal que coincida con el ID.
        branch = next((b for b in self._branches if b.branch_id == branch_id), None)
        
        # Si la encontramos, la devolvemos (convertida a diccionario).
        # Si no la encontramos (branch es None), devolvemos None.
        return branch.to_dict() if branch else None