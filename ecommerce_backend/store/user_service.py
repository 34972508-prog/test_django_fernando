# store/user_service.py
import json
import os
# Importamos los "moldes" de usuario de models.py
from .models import AdminUser, ClientUser

# Definimos la ruta de la "base de datos" de usuarios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'data', 'users.json')

class UserService:
    
    def __init__(self):
        # self._users contendrá una lista de OBJETOS
        # (algunos AdminUser, otros ClientUser)
        self._users = self._load_users()

    def _load_users(self):
        """
        Carga el JSON y decide qué "molde" (AdminUser o ClientUser) usar
        para cada item.
        """
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_objects = []
                for item in data:
                    # Preparamos los argumentos comunes (email/address pueden ser None)
                    args = (item['id'], item['username'], item['password'], item.get('email'), item.get('address'))
                    
                    # --- Polimorfismo ---
                    # Decidimos qué objeto crear basado en el 'role' del JSON
                    if item['role'] == 'admin':
                        # Creamos un objeto AdminUser
                        user_objects.append(AdminUser(*args))
                    else:
                        # Creamos un objeto ClientUser
                        user_objects.append(ClientUser(*args))
                
                return user_objects
                
        except (FileNotFoundError, json.JSONDecodeError):
            # Si el archivo no existe o está vacío, lo creamos.
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                # Creamos el usuario 'admin' por defecto.
                admin_data = {
                    "id": 1, "username": "admin", 
                    "password": "adminpassword123", "role": "admin",
                    "email": "admin@test.com", "address": "N/A"
                }
                json.dump([admin_data], f, indent=4)
                # Devolvemos una lista con el objeto AdminUser
                return [AdminUser(admin_data['id'], admin_data['username'], admin_data['password'],
                                  admin_data['email'], admin_data['address'])] 
            
    def _save_users(self):
        """
        Guarda la lista de OBJETOS de usuario de nuevo en el JSON.
        """
        # Llama al método .to_dict() de CADA objeto (sea Admin o Client)
        users_as_dicts = [u.to_dict() for u in self._users]
        
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_as_dicts, f, indent=4, ensure_ascii=False)

    # --- Métodos Públicos (APIs del Servicio) ---

    def get_user_by_username(self, username):
        """
        Busca un usuario por 'username'.
        Devuelve el OBJETO de usuario completo (o None).
        """
        if not username:
            return None
        # Comparamos usando la propiedad .username del objeto
        return next((u for u in self._users if u.username.lower() == username.lower()), None)
    
    def get_user_by_id(self, user_id):
        """
        Busca un usuario por 'ID'.
        Devuelve el OBJETO de usuario completo (o None).
        """
        print(f"DEBUG UserService - Buscando usuario con ID: {user_id}")
        if not user_id:
            return None
        
        # Comparamos usando la propiedad .user_id del objeto
        user = next((u for u in self._users if u.user_id == user_id), None)
        
        if user:
            print(f"DEBUG UserService - Usuario encontrado: {user.username}")
        else:
            print(f"DEBUG UserService - Usuario con ID {user_id} no encontrado")
        
        return user

    def create_user(self, username, password, email= None, address=None):
        """
        Crea un nuevo Cliente (ClientUser).
        """
        # 1. Verificamos que el nombre no esté en uso.
        if self.get_user_by_username(username):
            return None # El usuario ya existe

        try:
            # 2. Calculamos el nuevo ID (el máximo + 1)
            new_id = max([u.user_id for u in self._users], default=0) + 1
            
            # 3. Creamos el objeto (siempre de tipo ClientUser)
            new_user = ClientUser(
                user_id=new_id,
                username=username,
                password=password,
                email=email,
                address=address
            )
            
            # 4. Añadimos el objeto a la lista en memoria
            self._users.append(new_user)
            # 5. Guardamos la lista completa en el JSON
            self._save_users()
            
            # Devolvemos el diccionario del nuevo usuario
            return new_user.to_dict()
        except Exception as e:
            print(f"Error al crear usuario: {e}")
            return None
    

    def delete_user(self, user_id):
        """
        Elimina un usuario por su ID.
        """
        initial_count = len(self._users)
        
        # 1. Re-creamos la lista de usuarios, excluyendo al ID a borrar.
        #    Convertimos el user_id (que puede venir como str de la URL) a int.
        self._users = [u for u in self._users if u.user_id != int(user_id)]
        
        final_count = len(self._users)
        
        # 2. Si el contador bajó, es que SÍ se eliminó.
        if final_count < initial_count:
            # 3. Guardamos la lista actualizada en el JSON
            self._save_users()
            return True
        else:
            return False # No se encontró el ID