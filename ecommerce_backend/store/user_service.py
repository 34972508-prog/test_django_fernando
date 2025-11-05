# store/user_service.py
import json
import os
# Importamos las nuevas clases de modelos
from .models import AdminUser, ClientUser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'data', 'users.json')

class UserService:
    
    def __init__(self):
        # self._users ahora contendrá OBJETOS (AdminUser o ClientUser)
        self._users = self._load_users()

    def _load_users(self):
        """
        Carga el JSON e INSTANCIA las clases AdminUser o ClientUser.
        """
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_objects = []
                for item in data:
                    args = (item['id'], item['username'], item['password'])
                    
                    # Aquí ocurre la magia (Polimorfismo)
                    if item['role'] == 'admin':
                        user_objects.append(AdminUser(*args))
                    else:
                        user_objects.append(ClientUser(*args))
                
                return user_objects
                
        except (FileNotFoundError, json.JSONDecodeError):
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                # Si creamos el archivo, añadimos el admin por defecto
                admin_data = {
                    "id": 1, "username": "admin", 
                    "password": "adminpassword123", "role": "admin"
                }
                json.dump([admin_data], f, indent=4)
                # Devolvemos el objeto admin instanciado
                return [AdminUser(admin_data['id'], admin_data['username'], admin_data['password'])]
            
    def _save_users(self):
        """
        Convierte la lista de objetos de usuario a dicts y guarda en JSON.
        """
        # Llama al método to_dict() de cada objeto
        users_as_dicts = [u.to_dict() for u in self._users]
        
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_as_dicts, f, indent=4, ensure_ascii=False)

    def get_user_by_username(self, username):
        """
        Busca un usuario por su nombre de usuario.
        Devuelve el OBJETO de usuario o None.
        """
        if not username:
            return None
        # Ahora busca en la propiedad .username del objeto
        return next((u for u in self._users if u.username.lower() == username.lower()), None)

    def create_user(self, username, password):
        """
        Crea un nuevo objeto ClientUser, lo guarda y devuelve su dict.
        """
        if self.get_user_by_username(username):
            return None # El usuario ya existe

        try:
            new_id = max([u.user_id for u in self._users], default=0) + 1
            
            # Instancia la nueva clase
            new_user = ClientUser(
                user_id=new_id,
                username=username,
                password=password
            )
            
            self._users.append(new_user)
            self._save_users()
            
            # Devuelve el dict (para mantener consistencia con create_product)
            return new_user.to_dict()
        except Exception as e:
            print(f"Error al crear usuario: {e}")
            return None