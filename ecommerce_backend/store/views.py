# store/views.py
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .product_service import ProductService
from .decorators import admin_required

from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages

from .user_service import UserService 
from django.contrib import messages 

from uuid import uuid4
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .mixins import AdminRequiredMixin 

from .branch_service import BranchService 
from django.core.serializers.json import DjangoJSONEncoder
import json

# Inicializacion de los servicios (global para las vistas)
user_service = UserService()
product_service = ProductService()
branch_service = BranchService() # <-- Asegurarse que esté instanciado globalmente

class ProductListCreateAPIView(APIView):
    """
    Vista para listar productos (con filtros) y crear nuevos productos.
    Responde a la URL: /api/products/
    """
    def get(self, request):
        service = ProductService()
        query_params = request.query_params
        
        name_filter = query_params.get('name', None)
        category_id_str = query_params.get('category_id', None)
        
        category_id_filter = None
        if category_id_str:
            try:
                category_id_filter = int(category_id_str)
            except (ValueError, TypeError):
                return Response({"error": "category_id debe ser un número."}, status=status.HTTP_400_BAD_REQUEST)

        products = service.get_all_products(name_filter, category_id_filter)
        return Response(products, status=status.HTTP_200_OK)

    @method_decorator(admin_required)
    def post(self, request):
        service = ProductService()
        new_product = service.create_product(request.data)
        if new_product:
            return Response(new_product, status=status.HTTP_201_CREATED)
        return Response({"error": "Datos inválidos para crear producto"}, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailAPIView(APIView):
    """
    Vista para obtener, actualizar o eliminar un producto específico.
    Responde a la URL: /api/products/<int:pk>/
    """
    def get(self, request, pk):
        service = ProductService()
        product = service.get_product_by_id(pk)
        if product:
            return Response(product)
        return Response(status=status.HTTP_404_NOT_FOUND)

    @method_decorator(admin_required)
    def put(self, request, pk):
        service = ProductService()
        updated_product = service.update_product(pk, request.data)
        if updated_product:
            return Response(updated_product)
        return Response(status=status.HTTP_404_NOT_FOUND)

    @method_decorator(admin_required)
    def delete(self, request, pk):
        service = ProductService()
        if service.delete_product(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)

# --- VISTAS HTML PARA PRODUCTOS ---

class AdminProductView(AdminRequiredMixin,View):
    def get(self, request):
        service = ProductService()
        all_products = service.get_all_products()
        
        # --- MEJORA: Obtener nombres de categorías ---
        all_categories = service.get_all_categories()
        # Convertir a un mapa para búsqueda rápida: {1: 'Tortas', 2: 'Postres'}
        category_map = {cat['id']: cat['name'] for cat in all_categories}
        
        # Añadir el nombre de la categoría a cada producto
        for product in all_products:
            product['category_name'] = category_map.get(product['category_id'], 'Sin Categoría')
        # --- FIN DE LA MEJORA ---

        context = {
            'products': all_products,
        }
        return render(request, 'store/admin_products.html', context)


class ProductFormView(AdminRequiredMixin, View):
    """
    Vista para crear (GET, POST) y editar (GET, POST) productos.
    Requiere ser administrador.
    (ESTA ES LA VERSIÓN CORREGIDA Y ÚNICA)
    """
    template_name = 'store/product_form.html'
    
    # Usamos los servicios globales
    service = product_service
    branch_service = branch_service

    def get(self, request, pk=None):
        context = {}
        # Cargar categorías para el dropdown
        context['categories'] = self.service.get_all_categories()
        
        # --- ¡CORREGIDO! ---
        # Cargar sucursales para el dropdown
        context['branches'] = self.branch_service.get_all_branches()
        # --- FIN CORREGIDO ---

        if pk:
            # --- MODO EDICIÓN ---
            product = self.service.get_product_by_id(pk)
            if not product:
                messages.error(request, 'Producto no encontrado.')
                return redirect('admin-product-view')
            context['form_title'] = f'Editar Producto: {product["title"]}'
            context['product'] = product
            context['is_edit'] = True
        else:
            # --- MODO CREACIÓN ---
            context['form_title'] = 'Crear Nuevo Producto'
            context['is_edit'] = False

        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        data = request.POST.copy()
        
        # --- Lógica de datos (convertir a tipos correctos) ---
        try:
            data['price'] = float(data.get('price'))
            data['stock'] = int(data.get('stock'))
            data['category_id'] = int(data.get('category_id'))
            
            # --- ¡CORREGIDO! ---
            # Obtener y validar el ID de la sucursal
            branch_id_str = data.get('branch_id')
            if not branch_id_str:
                raise ValueError("La sucursal es obligatoria.")
            data['branch_id'] = int(branch_id_str)
            # --- FIN CORREGIDO ---

            weight = data.get('weight')
            data['weight'] = float(weight) if weight else None
            
        except (ValueError, TypeError) as e:
            messages.error(request, f'Datos inválidos. Verifica precio, stock, peso o IDs. Error: {e}')
            # Recargar el formulario con los datos anteriores y los dropdowns
            context = {
                'form_title': 'Crear Nuevo Producto' if not pk else 'Editar Producto',
                'is_edit': bool(pk),
                'product': data, # Devolver los datos POST para rellenar el formulario
                'categories': self.service.get_all_categories(),
                'branches': self.branch_service.get_all_branches() # ¡No olvidar!
            }
            return render(request, self.template_name, context)

        # --- Lógica de Imagen (Manejo de subida y URL) ---
        image_url_externa = data.get('image_url')
        image_file = request.FILES.get('image_file')

        if image_file:
            try:
                file_name = f"productos/{uuid4().hex}{os.path.splitext(image_file.name)[1]}"
                path = default_storage.save(file_name, ContentFile(image_file.read()))
                data['image_url'] = default_storage.url(path) # Sobrescribe cualquier URL
                
            except Exception as e:
                messages.error(request, f"Error al subir la imagen: {str(e)}")
                # Si falla la subida, se devuelve el control al formulario
                context = {
                    'form_title': 'Crear Nuevo Producto' if not pk else 'Editar Producto',
                    'is_edit': bool(pk),
                    'product': data,
                    'categories': self.service.get_all_categories(),
                    'branches': self.branch_service.get_all_branches()
                }
                return render(request, self.template_name, context)
        
        elif image_url_externa:
            data['image_url'] = image_url_externa
        
        elif pk:
            # Si es edición, no hay archivo nuevo ni URL, mantener la imagen anterior
            product_actual = self.service.get_product_by_id(pk)
            data['image_url'] = product_actual.get('image_url', '') # Mantener la URL anterior
        else:
            # Si es creación y no se provee nada
            data['image_url'] = '' 
        
        # --- Lógica de Creación/Actualización ---
        if pk:
            # --- ACTUALIZAR (EDITAR) ---
            product = self.service.update_product(pk, data)
            if product:
                messages.success(request, f'Producto "{product["title"]}" actualizado con éxito.')
            else:
                messages.error(request, 'Error al actualizar el producto.')
        else:
            # --- CREAR ---
            product = self.service.create_product(data)
            if product:
                messages.success(request, f'Producto "{product["title"]}" creado con éxito.')
            else:
                messages.error(request, 'Error al crear el producto.')

        return redirect('admin-product-view')


class DeleteProductHTMLView(AdminRequiredMixin,View):
    """
    Vista específica para eliminar productos desde el HTML
    """
    def post(self, request, pk):
        service = ProductService()
        
        if service.delete_product(pk):
            messages.success(request, f"Producto eliminado exitosamente")
        else:
            messages.error(request, f"Error al eliminar el producto")
        
        return redirect('admin-product-view')


class List_productView(View):
    """
    Vista para listar productos en HTML (catálogo público)
    Responde a la URL: /products/list
    """
    def get(self, request):
        service = ProductService()
        productos = service.get_all_products()
        
        context = {
            'productos': productos,
            'titulo': 'Catálogo de Productos'
        }
        return render(request, 'store/list_product.html', context)


class ProductDetailHTMLView(View):
    """
    Muestra la página detalle de un producto (HTML).
    URL: /products/<pk>/view/  (nombre: product-detail-html)
    """
    def get(self, request, pk):
        service = ProductService()
        product = service.get_product_by_id(pk)
        if not product:
            messages.error(request, "Producto no encontrado")
            return redirect('product-list-html')
        
        context = {
            'producto': product,
            'titulo': product.get('title', 'Detalle del producto')
        }
        # 🔑 CLAVE: Determinar qué template renderizar
        if request.GET.get('modal') == 'true':
            return render(request, 'store/product_detail_modal_fragment.html', context)
        else:
            return render(request, 'store/product_detail.html', context)

    
# --- VISTAS HTML PARA CATEGORÍAS (VERSIÓN ÚNICA Y CORRECTA) ---

class AdminCategoryView(AdminRequiredMixin,View):
    """
    Vista para listar todas las categorías en una tabla HTML.
    """
    def get(self, request):
        service = ProductService()
        all_categories = service.get_all_categories()
        context = {
            'categories': all_categories,
        }
        return render(request, 'store/admin_categories.html', context)


class CategoryFormView(AdminRequiredMixin,View):
    """
    Vista para mostrar y procesar el formulario de
    CREACIÓN o EDICIÓN de categorías.
    """
    def get(self, request, pk=None):
        service = ProductService()
        category_data = None
        form_title = "Crear Nueva Categoría"

        if pk:
            category_data = service.get_category_by_id(pk)
            if not category_data:
                messages.error(request, "Categoría no encontrada")
                return redirect('admin-category-view') 
            form_title = f"Editar Categoría: {category_data.get('name')}"

        context = {
            'form_title': form_title,
            'category': category_data,
            'is_edit': pk is not None,
            'pk': pk
        }
        return render(request, 'store/category_form.html', context)

    def post(self, request, pk=None):
        service = ProductService()
        category_name = request.POST.get('name')

        if not category_name:
            messages.error(request, "El nombre de la categoría no puede estar vacío.")
            return render(request, 'store/category_form.html', {'name': category_name})

        if pk:
            updated_category = service.update_category(pk, {'name': category_name})
            if updated_category:
                messages.success(request, f"Categoría '{category_name}' actualizada exitosamente.")
                return redirect('admin-category-view') 
            else:
                messages.error(request, "Error al actualizar la categoría.")
                return redirect('category-edit', pk=pk)
        else:
            new_category = service.create_category({'name': category_name})
            if new_category:
                messages.success(request, f"Categoría '{category_name}' creada exitosamente.")
                return redirect('admin-category-view')
            else:
                messages.error(request, "Error al guardar la categoría.")
                return render(request, 'store/category_form.html', {'name': category_name})

class DeleteCategoryView(AdminRequiredMixin,View):
    """
    Vista específica para eliminar categorías desde el HTML (POST).
    """
    def post(self, request, pk):
        service = ProductService()
        
        if service.delete_category(pk):
            messages.success(request, f"Categoría eliminada exitosamente.")
        else:
            messages.error(request, f"Error al eliminar la categoría. Asegúrate de que no esté en uso por ningún producto.")
        
        return redirect('admin-category-view') 


# --- VISTAS DE CARRITO Y CHECKOUT ---

class CartView(View):
    def get(self, request):
        cart = request.session.get('cart', {})
        service = ProductService()
        cart_items = []
        total = 0
        
        for product_id, quantity in cart.items():
            product = service.get_product_by_id(int(product_id))
            if product:
                item_total = product['price'] * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total': item_total
                })
                total += item_total
        
        context = {
            'cart_items': cart_items,
            'total': total
        }
        return render(request, 'store/cart.html', context)

    def post(self, request):
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        
        if not product_id:
            messages.error(request, "Producto no válido")
            return redirect('cart')
            
        cart = request.session.get('cart', {})
        
        if action == 'add':
            quantity = int(request.POST.get('quantity', 1))
            if product_id in cart:
                cart[product_id] += quantity
            else:
                cart[product_id] = quantity
            messages.success(request, "Producto agregado al carrito")
            
        elif action == 'remove':
            if product_id in cart:
                del cart[product_id]
                messages.success(request, "Producto eliminado del carrito")
                
        request.session['cart'] = cart
        return redirect('cart')


class CheckoutView(View):
    def get(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            messages.warning(request, "Tu carrito está vacío")
            return redirect('cart')
            
        service = ProductService()
        cart_items = []
        total = 0
        
        for product_id, quantity in cart.items():
            product = service.get_product_by_id(int(product_id))
            if product:
                item_total = product['price'] * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total': item_total
                })
                total += item_total
                
        context = {
            'cart_items': cart_items,
            'total': total
        }
        return render(request, 'store/checkout.html', context)

    def post(self, request):
        try:
            cart = request.session.get('cart', {})
            if not cart:
                raise ValueError("Carrito vacío")
                
            request.session['cart'] = {}
            messages.success(request, "¡Pago procesado con éxito! Gracias por tu compra.")
            return redirect('order-confirmation')
            
        except Exception as e:
            messages.error(request, f"Error al procesar el pago: {str(e)}")
            return redirect('checkout')


# --- VISTAS DE AUTENTICACIÓN (Simuladas con JSON) ---

class LoginView(View):
    
    def get(self, request):
        if request.session.get('user_id'):
            return redirect('home')
        return render(request, 'store/login.html')

    def post(self, request):
        service = UserService()
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = service.get_user_by_username(username)
        
        if user and user.password == password:
            
            request.session['user_id'] = user.user_id
            request.session['username'] = user.username
            request.session['user_role'] = user.role
            
            messages.success(request, f"¡Bienvenido, {user.username}!")
            
            if user.role == 'admin':
                return redirect('admin-product-view')
            else:
                return redirect('product-list-html')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, 'store/login.html')

class RegisterView(View):
    
    def get(self, request):
        if request.session.get('user_id'):
            return redirect('home')
        return render(request, 'store/register.html')

    def post(self, request):
        service = UserService()
        username = request.POST.get('username')
        pass1 = request.POST.get('password')
        pass2 = request.POST.get('password2')
        
        if not username or not pass1 or not pass2:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, 'store/register.html')
            
        if pass1 != pass2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'store/register.html')

        new_user = service.create_user(username, pass1)
        
        if new_user:
            request.session['user_id'] = new_user['id']
            request.session['username'] = new_user['username']
            request.session['user_role'] = new_user['role']
            
            messages.success(request, "¡Registro exitoso! Has iniciado sesión.")
            return redirect('product-list-html') 
        else:
            messages.error(request, "El nombre de usuario ya existe.")
            return render(request, 'store/register.html')

class LogoutView(View):
    def get(self, request):
        try:
            request.session.flush()
            messages.success(request, "Has cerrado sesión exitosamente.")
        except Exception as e:
            print(f"Error al cerrar sesión: {e}")
            
        return redirect('home')


# --- VISTAS DE USUARIOS Y PERFIL ---

class AdminUserView(AdminRequiredMixin, View):
    """
    Vista para listar todos los usuarios (Admin View).
    """
    def get(self, request):
        
        all_users = user_service._users # Accede directamente a la lista cargada
        
        context = {
            'users': all_users, 
            'titulo': 'Administración de Usuarios'
        }
        return render(request, 'store/admin_users.html', context)
        

class DeleteUserHTMLView(AdminRequiredMixin, View):
    """
    Vista para manejar la eliminación de usuarios.
    """
    def post(self, request, pk):
        if user_service.delete_user(pk):
            messages.success(request, f"Usuario con ID {pk} eliminado exitosamente.")
        else:
            messages.error(request, f"Error al eliminar el usuario con ID {pk}.")
        
        return redirect('admin-user-view')


def profile_view(request):
    """
    Muestra el perfil del usuario logueado.
    """
    logged_in_username = request.session.get('username')
    
    if not logged_in_username:
        messages.warning(request, "Debes iniciar sesión para ver tu perfil.")
        return redirect('login') 
    
    user_object = user_service.get_user_by_username(logged_in_username)
    
    if not user_object:
        request.session.flush() 
        messages.error(request, "Perfil no encontrado. Inicia sesión de nuevo.")
        return redirect('login')
        
    context = {
        'user': user_object, 
        'username': user_object.username,
        'is_admin': user_object.role == 'admin', 
    }
    
    return render(request, 'store/profile_user.html', context)

# --- VISTA DE SUCURSALES ---

class AdminBranchView(AdminRequiredMixin, View):
    """
    Vista para listar todas las sucursales (solo admin).
    """
    template_name = 'store/admin_branches.html'
    service = BranchService()

    def get(self, request):
        branches = self.service.get_all_branches()
        
        context = {
            'branches': branches,
            # --- 🛑 ¡CORRECCIÓN! 🛑 ---
            # Quitamos json.dumps. La etiqueta |json_script se encarga de esto.
            'branches_json': branches
        }
        return render(request, self.template_name, context)