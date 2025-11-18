## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/34972508-prog/QuieroalgoDulce2025.git

# 2. Navegar al directorio del proyecto
cd QuieroalgoDulce2025

# 3. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ir a la carpeta ecommerce_backend
cd ecommerce_backend

# 6. Migrar base unica ves en todo el proyecto
python manage.py migrate

# 7. Ir a la carpeta ecommerce_backend
cd ecommerce_backend

# 8. Ejecutar el servidor de desarrollo
python manage.py runserver


<div align="center">

⭐ ¿Te gustó el proyecto? ¡Dale una estrella al repositorio!

Hecho con ❤️ y mucho ☕ para Seminario de Lenguaje 1

</div>



Acceso al Sistema

Una vez ejecutado, acceder a: http://127.0.0.1:8000

🔐 Usuarios de Prueba

👤 Cliente Demo

· Usuario: Alice
· Contraseña: alice123
· Acceso: Todas las funcionalidades de compra

👑 Administrador Demo

· Usuario: admin
· Contraseña: adminpassword123
· Acceso: Panel administrativo completo

📊 Modelos Principales

🏪 Branch (Sucursal)

python
class Branch:
    def __init__(self, branch_id, name, address, latitude, longitude, 
                 is_open, opening_hours, phone):
    # Representa una sucursal física con geolocalización


🎂 Product (Sistema de Productos)

python
class Product(ABC):  # Clase abstracta base
class CakeProduct(Product):  # Implementación específica para tortas
    # Productos con categorías, stock y asignación a sucursales


👥 Sistema de Usuarios

python
class BaseUser(ABC):  # Clase abstracta base
class ClientUser(BaseUser):  # Usuarios cliente
class AdminUser(BaseUser):   # Usuarios administradores
    # Sistema de roles y autenticación


🛒 Gestión de Carritos

python
class Cart:
    # Carrito de compras persistente por usuario
class CartItem:
    # Items individuales en el carrito


🛡️ Sistema de Seguridad

🔒 Autenticación y Autorización

· Validación de Credenciales - Verificación contra archivos JSON
· Control de Roles - Separación clara entre ClientUser y AdminUser
· Decoradores de Seguridad - @admin_required, @client_required
· Gestión de Sesiones - Manejo seguro de sesiones Django

🚫 Protección de Vistas

python
@admin_required
def admin_dashboard(request):
    # Solo accesible para administradores

@client_required
def client_cart(request):
    # Solo accesible para clientes


🌐 APIs Disponibles

El sistema incluye APIs RESTful para integración:

· GET /api/products/ - Lista de productos
· GET /api/branches/ - Sucursales disponibles
· POST /api/cart/ - Gestión de carrito
· GET /api/orders/ - Órdenes de usuario

🎯 Flujos Principales

🛒 Proceso de Compra del Cliente

1. Selección de Sucursal → Elige ubicación preferida
2. Exploración de Catálogo → Productos disponibles en esa sucursal
3. Gestión de Carrito → Agrega, modifica o elimina productos
4. Proceso de Pago → Completa la compra
5. Confirmación de Orden → Recibe número de seguimiento

⚙️ Flujo Administrativo

1. Dashboard Overview → Vista general del negocio
2. Gestión de Inventario → Control de productos y stock
3. Monitoreo de Ventas → Seguimiento de órdenes y carritos
4. Administración → Gestión de usuarios y sucursales

📱 Características Técnicas Avanzadas

🔄 Arquitectura MVC

· Models - Clases Python para representar datos
· Views - Controladores Django que manejan la lógica
· Templates - Vistas HTML con integración Bootstrap

💾 Persistencia de Datos

· JSON como Base de Datos - Ideal para prototipos y proyectos académicos
· Servicios Dedicados - Clases especializadas para operaciones CRUD
· Validación de Integridad - Verificación de datos antes de persistir

🎨 Experiencia de Usuario

· Diseño Responsive - Adaptable a dispositivos móviles y desktop
· Interfaz Intuitiva - Navegación simple y clara
· Feedback Inmediato - Mensajes de confirmación y error

