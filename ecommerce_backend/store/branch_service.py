# store/branch_service.py
import json
import os
from .models import Branch # Importaremos el modelo Branch que añadiremos a models.py

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRANCHES_FILE = os.path.join(BASE_DIR, 'data', 'sucursales.json')

class BranchService:
    def __init__(self):
        self._branches = self._load_branches()

    def _load_branches(self):
        """Carga el JSON de sucursales e instancia objetos Branch."""
        try:
            with open(BRANCHES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [
                    Branch(
                        branch_id=b['id'],
                        name=b['name'],
                        address=b['address'],
                        latitude=b['latitude'],
                        longitude=b['longitude']
                    ) for b in data
                ]
        
        # --- ¡MODIFICACIÓN CLAVE PARA DEPURAR! ---
        # Ahora capturamos CUALQUIER error y lo mostramos
        except Exception as e: 
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR GRAVE AL CARGAR SUCURSALES: {e}")
            print(f"La ruta del archivo que se intentó leer es:")
            print(BRANCHES_FILE)
            print("Por favor, verifica que el archivo exista y que el JSON sea válido.")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            return [] # Devolvemos vacío, pero ya mostramos el error
        # --- FIN DE LA MODIFICACIÓN ---


    def get_all_branches(self):
        """Devuelve una lista de diccionarios de todas las sucursales."""
        return [b.to_dict() for b in self._branches]

    def get_branch_by_id(self, branch_id):
        """Busca una sucursal por ID y devuelve su diccionario."""
        branch = next((b for b in self._branches if b.branch_id == branch_id), None)
        return branch.to_dict() if branch else None