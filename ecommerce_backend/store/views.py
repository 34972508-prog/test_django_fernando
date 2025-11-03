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

# ... (imports existentes)
from .user_service import UserService # <-- AÑADIR
from django.contrib import messages # <-- AÑADIR

# Se usan default_storage para el manejo de archivos local o en la nube (S3)
from uuid import uuid4
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# ... (imports existentes)
from .mixins import AdminRequiredMixin # <-- AÑADIR

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

# 🛑 INICIO DE LA CORRECCIÓN EN views.py 🛑
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
# 🛑 FIN DE LA CORRECCIÓN EN views.py 🛑


class ProductFormView(AdminRequiredMixin,View):
    """
    Vista dedicada para mostrar el formulario de creación o edición, 
    y manejar el envío (POST) de esos formularios.
    """
    
    #@method_decorator(admin_required)
    def get(self, request, pk=None):
        service = ProductService()

        # Pide las categorías para el combo
        all_categories = service.get_all_categories() 
       
        product_data = None
        form_title = "Crear Nuevo Producto"

        # Modo Edición
        if pk is not None:
            product_data = service.get_product_by_id(pk)
            if not product_data:
                messages.error(request, "Producto no encontrado")
                return redirect('admin-product-view')
            form_title = f"Editar Producto "
        
        context = {
            'form_title': form_title,
            'product': product_data,
            'is_edit': pk is not None,
            'pk': pk,
            'categories': all_categories  # Pásalas al template
        }
        return render(request, 'store/product_form.html', context)

    #@method_decorator(admin_required)
    def post(self, request, pk=None):
        service = ProductService()

        # Obtener datos del formulario
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category_id')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        weight = request.POST.get('weight')

        # Manejo de la imagen subida
        image_file = request.FILES.get('image_file')
        # Mantiene la URL existente si no se sube una nueva
        image_url = request.POST.get('image_url', '') 
        
        if image_file:
            try:
                # Genera un nombre único y la ruta de guardado (dentro de la subcarpeta 'productos')
                file_name = f"productos/{uuid4().hex}{os.path.splitext(image_file.name)[1]}"
                
                # Guarda el archivo usando el sistema de almacenamiento por defecto (local o S3)
                path = default_storage.save(file_name, ContentFile(image_file.read()))
                
                # Obtiene la URL/Path que el template debe usar (ej: /media/productos/xyz.jpg o URL S3)
                image_url = default_storage.url(path)
                
            except Exception as e:
                messages.error(request, f"Error al subir la imagen: {str(e)}")
                # Si falla la subida, se devuelve el control al formulario
                return redirect('product-create' if not pk else 'product-edit', pk=pk)
            
        # Validaciones básicas
        if not title or not price or not stock or not category_id:
            error_msg = "Título, categoría, precio y stock son campos obligatorios"
            messages.error(request, error_msg)
            if pk:
                return redirect('product-edit', pk=pk)
            else:
                return redirect('product-create')

        try:
            # Preparar datos para el servicio
            product_data = {
                'title': title,
                'description': description or '',
                'category_id': int(category_id),
                'price': float(price),
                'stock': int(stock),
                'image_url': image_url or '', # Usa la URL/Path generada o la existente
                'weight': float(weight) if weight else 0.0,
                'type': 'cake'  # Valor por defecto
            }
        except (ValueError, TypeError) as e:
            error_msg = f"Error en el formato de los datos: {str(e)}"
            messages.error(request, error_msg)
            if pk:
                return redirect('product-edit', pk=pk)
            else:
                return redirect('product-create')

        # Lógica de creación o edición
        if pk is None:
            new_product = service.create_product(product_data)
            if new_product:
                messages.success(request, "Producto creado exitosamente")
                return redirect('admin-product-view')
            else:
                messages.error(request, "Error al crear el producto")
                return redirect('product-create')
        else:          
            updated_product = service.update_product(pk, product_data)
            if updated_product:
                messages.success(request, "Producto actualizado exitosamente")
                return redirect('admin-product-view')
            else:
                messages.error(request, "Error al actualizar el producto")
                return redirect('product-edit', pk=pk)

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
        # Verificamos si la solicitud incluye el query param 'modal=true'
        if request.GET.get('modal') == 'true':
            # Si es una solicitud AJAX para el modal, devolvemos el fragmento
            return render(request, 'store/product_detail_modal_fragment.html', context)
        else:
            # Si es navegación normal (vista de cliente), devolvemos la página completa
            return render(request, 'store/product_detail.html', context)

    
   
# (Estas vistas están correctas y no requieren cambios)

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
            # Modo Edición: Obtenemos los datos de la categoría
            category_data = service.get_category_by_id(pk)
            if not category_data:
                messages.error(request, "Categoría no encontrada")
                return redirect('admin-category-view') # Redirige a la lista de categorías
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
            # Modo Edición (Actualizar)
            updated_category = service.update_category(pk, {'name': category_name})
            if updated_category:
                messages.success(request, f"Categoría '{category_name}' actualizada exitosamente.")
                return redirect('admin-category-view') # Redirige a la lista
            else:
                messages.error(request, "Error al actualizar la categoría.")
                return redirect('category-edit', pk=pk)
        else:
            # Modo Creación
            new_category = service.create_category({'name': category_name})
            if new_category:
                messages.success(request, f"Categoría '{category_name}' creada exitosamente.")
                return redirect('admin-category-view') # Redirige a la lista
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
            # El servicio devuelve False si no se encuentra o si está en uso
            messages.error(request, f"Error al eliminar la categoría. Asegúrate de que no esté en uso por ningún producto.")
        
        return redirect('admin-category-view') # Redirige a la lista de categorías
    


# --- VISTAS HTML PARA CATEGORÍAS ---
# (Estas vistas están correctas y no requieren cambios)

class AdminCategoryView(View):
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
    

class CartView(View):
    def get(self, request):
        # Obtener o crear carrito en sesión
        cart = request.session.get('cart', {})
        
        # Obtener productos del carrito
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


class CategoryFormView(View):
    """
    Vista para mostrar y procesar el formulario de
    CREACIÓN o EDICIÓN de categorías.
    """
    
    def get(self, request, pk=None):
        service = ProductService()
        category_data = None
        form_title = "Crear Nueva Categoría"

        if pk:
            # Modo Edición: Obtenemos los datos de la categoría
            category_data = service.get_category_by_id(pk)
            if not category_data:
                messages.error(request, "Categoría no encontrada")
                return redirect('admin-category-view') # Redirige a la lista de categorías
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
            # Modo Edición (Actualizar)
            updated_category = service.update_category(pk, {'name': category_name})
            if updated_category:
                messages.success(request, f"Categoría '{category_name}' actualizada exitosamente.")
                return redirect('admin-category-view') # Redirige a la lista
            else:
                messages.error(request, "Error al actualizar la categoría.")
                return redirect('category-edit', pk=pk)
        else:
            # Modo Creación
            new_category = service.create_category({'name': category_name})
            if new_category:
                messages.success(request, f"Categoría '{category_name}' creada exitosamente.")
                return redirect('admin-category-view') # Redirige a la lista
            else:
                messages.error(request, "Error al guardar la categoría.")
                return render(request, 'store/category_form.html', {'name': category_name})

class DeleteCategoryView(View):
    """
    Vista específica para eliminar categorías desde el HTML (POST).
    """
    def post(self, request, pk):
        service = ProductService()
        
        if service.delete_category(pk):
            messages.success(request, f"Categoría eliminada exitosamente.")
        else:
            # El servicio devuelve False si no se encuentra o si está en uso
            messages.error(request, f"Error al eliminar la categoría. Asegúrate de que no esté en uso por ningún producto.")
        
        return redirect('admin-category-view') # Redirige a la lista de categorías


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
        # Aquí irá la lógica de procesamiento del pago
        try:
            # Simular procesamiento de pago
            cart = request.session.get('cart', {})
            if not cart:
                raise ValueError("Carrito vacío")
                
            # Limpiar el carrito después del pago exitoso
            request.session['cart'] = {}
            messages.success(request, "¡Pago procesado con éxito! Gracias por tu compra.")
            return redirect('order-confirmation')
            
        except Exception as e:
            messages.error(request, f"Error al procesar el pago: {str(e)}")
            return redirect('checkout')


# --- VISTAS DE AUTENTICACIÓN (Simuladas con JSON) ---

# --- DENTRO DE store/views.py ---

    # ... (deja todas las otras vistas como están) ...

    # =======================================
    # VISTAS DE AUTENTICACIÓN (Simuladas con JSON)
    # =======================================

class LoginView(View):
    
    def get(self, request):
        if request.session.get('user_id'):
            return redirect('home')
        return render(request, 'store/login.html')

    def post(self, request):
        service = UserService()
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 'user' es ahora un OBJETO (AdminUser o ClientUser) o None
        user = service.get_user_by_username(username)
        
        # --- 🛑 ESTA ES LA CORRECCIÓN ---
        # Cambiamos user['password'] por user.password
        if user and user.password == password:
            
            # ¡ÉXITO! Guardamos las propiedades del OBJETO en la sesión
            # Cambiamos ['id'] por .user_id
            # Cambiamos ['username'] por .username
            # Cambiamos ['role'] por .role
            request.session['user_id'] = user.user_id
            request.session['username'] = user.username
            request.session['user_role'] = user.role
            
            messages.success(request, f"¡Bienvenido, {user.username}!")
            
            # Usamos la propiedad .role
            if user.role == 'admin':
                return redirect('admin-product-view')
            else:
                return redirect('product-list-html')
        else:
            # Fallo
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, 'store/login.html')

# ... (El resto de las vistas RegisterView y LogoutView quedan igual) ...
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

        # Intentar crear el usuario
        new_user = service.create_user(username, pass1)
        
        if new_user:
            # Loguear al usuario automáticamente
            request.session['user_id'] = new_user['id']
            request.session['username'] = new_user['username']
            request.session['user_role'] = new_user['role']
            
            messages.success(request, "¡Registro exitoso! Has iniciado sesión.")
            return redirect('product-list-html') # Redirigir a la lista de productos
        else:
            messages.error(request, "El nombre de usuario ya existe.")
            return render(request, 'store/register.html')

class LogoutView(View):
    def get(self, request):
        try:
            # Limpiar la sesión de Django
            request.session.flush()
            messages.success(request, "Has cerrado sesión exitosamente.")
        except Exception as e:
            print(f"Error al cerrar sesión: {e}")
            
        return redirect('home')

