# store/views.py
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .product_service import ProductService
from .decorators import admin_required
from .cart_service import CartService # <-- Importado
from .order_service import OrderService


from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages

from .user_service import UserService 
from django.contrib import messages 
from django.views.generic import TemplateView
from uuid import uuid4
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .mixins import AdminRequiredMixin 

from .branch_service import BranchService 
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json


# Inicializacion de los servicios (global para las vistas)
user_service = UserService()
product_service = ProductService()
branch_service = BranchService() 
cart_service = CartService() #  Instancia del servicio de carrito (Checkout y Órdenes)

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
        return Response(status=status.HTTP_404_NOT_FOUND) # Corregí el typo 44 a 404

# --- VISTAS HTML PARA PRODUCTOS ---

class AdminProductView(AdminRequiredMixin,View):
    def get(self, request):
        service = ProductService()
        
        # Verificar si hay un filtro de sucursal activo en la sesión del administrador
        branch_id_filter = request.session.get('admin_product_filter_branch_id')
        filter_message = "(Mostrando todos)"
        branch_name = None # Vble para el nombre de la sucursal filtrada

        all_products = service.get_all_products()

        if branch_id_filter:
           # Obtener el nombre de la sucursal para mostrar en el título
            selected_branch = branch_service.get_branch_by_id(branch_id_filter) 
            
            if selected_branch:
                branch_name = selected_branch.get('name', f"ID: {branch_id_filter}") # Obtiene el nombre
                filter_message = f" en Sucursal {branch_name}" # Mensaje mejorado
            else:
                filter_message = f" (Filtrado por Sucursal ID: {branch_id_filter}, nombre no encontrado)"


            # Filtrar los productos localmente
            all_products = [
                p for p in all_products 
                if p.get('branch_id') == branch_id_filter
            ]
            
        
        
        # Enriquecer productos con el nombre de su categoría
        all_categories = service.get_all_categories()
        # Convertir a un mapa para búsqueda rápida: {1: 'Tortas', 2: 'Postres'}
        category_map = {cat['id']: cat['name'] for cat in all_categories}
        
        # Añadir el nombre de la categoría a cada producto
        for product in all_products:
            product['category_name'] = category_map.get(product['category_id'], 'Sin Categoría')

        context = {
            'products': all_products,
            'filter_message': filter_message,
            'show_clear_filter': branch_id_filter is not None # Para mostrar el botón de limpiar filtro
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
        
        # Cargar sucursales para el dropdown
        context['branches'] = self.branch_service.get_all_branches()
    
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
        
        try:
            data['price'] = float(data.get('price'))
            data['stock'] = int(data.get('stock'))
            data['category_id'] = int(data.get('category_id'))
            
            
            # Obtener y validar el ID de la sucursal
            branch_id_str = data.get('branch_id')
            if not branch_id_str:
                raise ValueError("La sucursal es obligatoria.")
            data['branch_id'] = int(branch_id_str)

            weight = data.get('weight')
            data['weight'] = float(weight) if weight else None
            
        except (ValueError, TypeError) as e:
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
                # Guardar imagen nueva en el servidor
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
        branch_service = BranchService()

        # Obtener la sucursal que el cliente eligió previamente
        selected_branch_id = request.session.get('selected_branch_id')

        all_products = service.get_all_products() 

        if selected_branch_id:
            # Filtrar productos por sucursal
            branch_id = int(selected_branch_id)
            productos = [prod for prod in all_products if prod.get('branch_id') == branch_id]
            
            branches = branch_service.get_all_branches()
            # Buscar el nombre de la sucursal para el título
            branch_name = next((b['name'] for b in branches if b['id'] == branch_id), "Catálogo")
            #branch_name = f" (Sucursal ID: {branch_id})"  # ME da el Id de la sucursal seleccionada
        else:
            # Si no hay sucursal seleccionada, No mostrar productos hasta que se seleccione una
            productos = []
            branch_name = " (Por favor selecciona una sucursal)"
        
        # Preparar el contexto para el template
        context = {
            'productos': productos,
            'titulo': f'Catálogo de Productos - Sucursal {branch_name}',
            # Flag para JS: muestra el modal si la sucursal no está seleccionada
            'show_branch_modal': selected_branch_id is None, # Activa el modal si es necesario
            'user_role': request.session.get('user_role')
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

        selected_branch_id = request.session.get('selected_branch_id')
        is_admin = request.session.get('user_role') == 'admin'

        if not product:
            messages.error(request, "Producto no encontrado")
            return redirect('product-list-html')

        # Si es cliente, verificar que el producto pertenezca a su sucursal seleccionada
        if not is_admin and selected_branch_id and product.get('branch_id') != int(selected_branch_id):
            messages.warning(request, "El producto no está disponible en la sucursal seleccionada.")
            return redirect('product-list-html')

         # Preparar el contexto para el template
        
        context = {
            'producto': product,
            'titulo': product.get('title', 'Detalle del producto')
        }
        # Si la petición es AJAX (modal), renderiza solo el fragmento
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
    """
    Vista para mostrar y gestionar el carrito de un usuario.
    Utiliza CartService para persistir los datos en carts.json.
    """
    
    def get(self, request):
        """
        Muestra el carrito del usuario logueado.
        """
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Debes iniciar sesión para ver tu carrito.")
            return redirect('login')
        
        # Recuperar el carrito del usuario
        cart = cart_service.get_cart(user_id)
        
        # Calcular totales y obtener detalles de productos
        cart_items = []
        total = 0
        for item in cart.items.values():
            product = product_service.get_product_by_id(item.product_id)
            if product:
                subtotal = product['price'] * item.quantity
                cart_items.append({
                    'product': product,
                    'quantity': item.quantity,
                    'subtotal': subtotal
                })
                total += subtotal
        
        context = {
            'cart_items': cart_items,
            'total': total
        }
        return render(request, 'store/cart.html', context)

    def post(self, request):
        """
        Agrega o elimina productos del carrito del usuario logueado.
        """
        user_id = request.session.get('user_id')
        is_ajax = 'HTTP_X_REQUESTED_WITH' in request.META and request.META['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest'

        if not user_id:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
            messages.error(request, "Debes iniciar sesión para modificar tu carrito.")
            return redirect('login')

        action = request.POST.get('action')
        product_id_str = request.POST.get('product_id')

        if not product_id_str or not product_id_str.isdigit():
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Producto no válido'}, status=400)
            messages.error(request, "Producto no válido")
            return redirect('cart')
        
        product_id = int(product_id_str)
        cart = cart_service.get_cart(user_id)

        if action == 'add':
            # Esta acción VIENE DE AJAX (list_product.html)
            quantity = int(request.POST.get('quantity', 1))
            product = product_service.get_product_by_id(product_id)

            if not product:
                return JsonResponse({'success': False, 'error': 'Producto no encontrado'}, status=404)
            
            if product['stock'] >= quantity:
                cart.add_item(product_id, quantity)
                cart_service.save_cart(cart)
                # Responde JSON (esto arregla el error de "conexión")
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'No hay suficiente stock'})

        elif action == 'remove':
            cart.remove_item(product_id)
            cart_service.save_cart(cart)
            messages.success(request, "Producto eliminado del carrito")
            return redirect('cart') # Redirige de vuelta al carrito
        
        # Fallback
        if is_ajax:
             return JsonResponse({'success': False, 'error': 'Acción desconocida'}, status=400)
        messages.error(request, "Acción desconocida")
        return redirect('cart')

class CheckoutView(View):
    """
    Vista para el checkout. Muestra el resumen y procesa el pago.
    Utiliza CartService y OrderService.
    """
    
    def get(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Debes iniciar sesión para finalizar la compra.")
            return redirect('login')
            
        # Obtener carrito del servicio
        cart = cart_service.get_cart(user_id)
        if not cart.items:
            messages.warning(request, "Tu carrito está vacío")
            return redirect('cart')
            
        #Detalles de productos
        cart_items = []
        total = 0
        for item in cart.items.values():
            product = product_service.get_product_by_id(item.product_id)
            if product:
                item_total = product['price'] * item.quantity
                cart_items.append({
                    'product': product,
                    'quantity': item.quantity,
                    'total': item_total
                })
                total += item_total
                
        context = {
            'cart_items': cart_items,
            'total': total
        }
        return render(request, 'store/checkout.html', context)

    def post(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Tu sesión ha expirado.")
            return redirect('login')
            
        try:
            cart = cart_service.get_cart(user_id)
            if not cart.items:
                messages.error(request, "Tu carrito está vacío.")
                return redirect('cart')

            
            # 1. Validar Datos del Formulario
            items_con_detalles = []
            total_verificado = 0
            
            for item in cart.items.values():
                product = product_service.get_product_by_id(item.product_id)
                if not product:
                    messages.error(request, f"El producto ID {item.product_id} ya no existe.")
                    return redirect('cart')
                
                if product['stock'] < item.quantity:
                    messages.error(request, f"¡Stock insuficiente para '{product['title']}'! Disponible: {product['stock']}.")
                    return redirect('cart')
                
                items_con_detalles.append({
                    'product': product, 
                    'quantity': item.quantity
                })
                total_verificado += product['price'] * item.quantity
            
            # Datos del formulario
            nombre = request.POST.get('nombre', '').strip()
            email = request.POST.get('email', '').strip()
            delivery_type = request.POST.get('delivery_type', 'pickup')
            direccion = request.POST.get('direccion', '')
            payment_method = request.POST.get('payment_method', 'cash')
            
            # Validar datos obligatorios
            if not nombre or not email:
                messages.error(request, "Por favor completa tu nombre y email.")
                return redirect('checkout')
            
            if delivery_type == 'delivery' and not direccion:
                messages.error(request, "Por favor ingresa tu dirección de envío.")
                return redirect('checkout')
            
            try:
                for item_detail in items_con_detalles:
                    product = item_detail['product']
                    cantidad_a_descontar = item_detail['quantity']
                    
                    # Descontar del stock
                    product['stock'] -= cantidad_a_descontar
                    
                    # Guardar cambios en el producto
                    product_service.update_product(product['id'], product)
                    
            except Exception as e:
                messages.error(request, f"Hubo un error al actualizar el stock: {e}")
                return redirect('checkout')
            
            # Obtener información del usuario
            user = user_service.get_user_by_id(user_id)
            
            # Crear user_data
            user_data = {
                "username": user.username if user else f"user_{user_id}",
                "email": email,
                "full_name": nombre,
                "delivery_type": delivery_type,
                "address": direccion if delivery_type == 'delivery' else "Retiro en local",
                "payment_method": payment_method
            }
            
            # Crear orden
            order_service = OrderService()

             # Obtener branch_id del primer producto
            branch_id = items_con_detalles[0]['product']['branch_id'] if items_con_detalles else None
            #Pasar los parámetros correctos al create_order
            order = order_service.create_order(
                user_id=user_id,
                cart_data=cart.to_dict(),
                user_data=user_data
            )
            
            # Limpiar carrito
            cart_service.remove_cart(user_id)
            
            request.session['last_order_id'] = order['id']
            
            messages.success(request, f"¡Pago procesado con éxito! Número de orden: #{order['id']}")
            return redirect('order-confirmation')
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"Error al procesar el pago: {str(e)}")
            return redirect('checkout')
        
class OrderHistoryView(View):
    """
    Vista para mostrar el historial de órdenes del usuario
    """
    def get(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Debes iniciar sesión para ver tu historial.")
            return redirect('login')
        
        order_service = OrderService()
        orders = order_service.get_orders_by_user(user_id)
        
        context = {
            'orders': orders
        }
        return render(request, 'store/order_history.html', context)

class OrderDetailView(View):
    """
    Vista para mostrar detalles de una orden específica
    """
    def get(self, request, order_id):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Debes iniciar sesión para ver los detalles de la orden.")
            return redirect('login')
        
        order_service = OrderService()
        order = order_service.get_order_by_id(order_id)
        
        # Verificar que la orden pertenece al usuario
        if not order or order['user_id'] != user_id:
            messages.error(request, "Orden no encontrada.")
            return redirect('order-history')
        
        context = {
            'order': order
        }
        return render(request, 'store/order_detail.html', context)
    
# --- NUEVA VISTA PARA ADMIN CARTS ---

class AdminCartsView(AdminRequiredMixin, View):
    """
    Vista de administrador para ver todos los carritos de compras
    almacenados en carts.json.
    """
    def get(self, request):
        # Cargar todos los carritos, devuelve un dict: {"user_id_1": {...}, "user_id_2": {...}}
        all_carts_data = cart_service.get_all_carts()
        
        processed_carts = []
        
        all_users = user_service._load_users()
        user_map = {str(u.user_id): u.username for u in all_users}

        for user_id_str, cart_data in all_carts_data.items():
            
            if not cart_data.get('items'):
                continue

            # Obtener info del usuario
            username = user_map.get(user_id_str, f"Usuario ID: {user_id_str} (No encontrado)")

            processed_items = []
            cart_total = 0
            
            for item_id_str, item_data in cart_data.get('items', {}).items():
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity', 0)
                
                product = product_service.get_product_by_id(product_id)
                
                if product:
                    product_name = product.get('title')
                    product_price = product.get('price', 0)
                    subtotal = product_price * quantity
                    cart_total += subtotal
                else:
                    product_name = f"Producto ID: {product_id} (No encontrado)"
                    subtotal = 0
                
                processed_items.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            
            processed_carts.append({
                'user_id': user_id_str,
                'username': username,
                'items': processed_items,
                'total': cart_total
            })

        context = {
            'carts': processed_carts
        }
        return render(request, 'store/admin_carts.html', context)

class AdminOrdersView(AdminRequiredMixin, View):
    """
    Vista de administrador para ver todas las órdenes
    """
    def get(self, request):
        order_service = OrderService()
        orders = order_service.get_all_orders()
        
        # Ordenar por fecha más reciente primero
        orders.sort(key=lambda x: x['created_at'], reverse=True)

         # Calcular estadísticas x estado
        status_counts = {
            'total': len(orders),
            'pending': 0,
            'confirmed': 0,
            'preparing': 0,
            'ready': 0,
            'completed': 0,
            'cancelled': 0
        }
        
        for order in orders:
            status = order.get('status', 'pending')
            if status in status_counts:
                status_counts[status] += 1
        
        context = {
            'orders': orders,
            'status_counts': status_counts
        }
        return render(request, 'store/admin_orders.html', context)

class AdminOrderDetailView(AdminRequiredMixin, View):
    """
    Vista de administrador para ver y gestionar una orden específica
    """
    def get(self, request, order_id):
        order_service = OrderService()
        order = order_service.get_order_by_id(order_id)
        
        if not order:
            messages.error(request, "Orden no encontrada.")
            return redirect('admin-orders')
        
        context = {
            'order': order
        }
        return render(request, 'store/admin_order_detail.html', context)
    
    def post(self, request, order_id):
        order_service = OrderService()
        new_status = request.POST.get('status')
        
        order = order_service.update_order_status(order_id, new_status)
        if order:
            messages.success(request, f"Orden #{order_id} actualizada a: {new_status}")
        else:
            messages.error(request, "Error al actualizar la orden.")
        
        return redirect('admin-order-detail', order_id=order_id)
# --- VISTAS DE AUTENTICACIÓN ---

class LoginView(View):
    
    def get(self, request):
        if request.session.get('user_id'):
            return redirect('home')
        return render(request, 'store/login.html')

    def post(self, request):
        service = UserService()
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Forzar recarga para reconocer usuarios nuevos
        user = service.get_user_by_username(username)
        
        if user and user.password == password:
            
            request.session['user_id'] = user.user_id
            request.session['username'] = user.username
            request.session['user_role'] = user.role
            
            
            if user.role == 'admin':
                return redirect('admin-product-view')
            else:
                # Si el cliente no tiene sucursal, irá a 'home'
                if not request.session.get('selected_branch_id'):
                     return redirect('home')
                return redirect('product-list-html')
        else:
            error_message = "Usuario o contraseña incorrectos. Por favor, intenta de nuevo."
            return render(request, 'store/login.html', {'error_message': error_message})
            
# --- VALIDACION  ---
class RegisterView(View):
    
    def get(self, request):
        if request.session.get('user_id'):
            return redirect('home')
        # Pasamos None para evitar errores si no hay datos en la sesión
        return render(request, 'store/register.html', {
            'username': None, 
            'email': None, 
            'address': None
        })

    def post(self, request):
        service = UserService()
        username = request.POST.get('username')
        pass1 = request.POST.get('password')
        pass2 = request.POST.get('password2')
        email = request.POST.get('email')
        address = request.POST.get('address')
        
        context_error = {
            'username': username,
            'email': email,
            'address': address
        }
        
        # VALIDACIÓN: Contraseña mínima 6 caracteres
        if len(pass1) < 6:
            context_error['error_message'] = "La contraseña debe tener al menos 6 caracteres."
            return render(request, 'store/register.html', context_error)
       
        if not username or not pass1 or not pass2 or not email:
            context_error['error_message'] = "Los campos de Usuario, Contraseña y Correo son obligatorios."
            # Pasamos el contexto de error de vuelta al template
            return render(request, 'store/register.html', context_error)
            
        if pass1 != pass2:
            context_error['error_message'] = "Las contraseñas no coinciden."
            return render(request, 'store/register.html', context_error)

        new_user = service.create_user(username, pass1, email= email, address = address)
        
        if new_user:
            request.session['user_id'] = new_user['id']
            request.session['username'] = new_user['username']
            request.session['user_role'] = new_user['role']
        
            # Redirigir a 'home' para que el modal de sucursal aparezca
            return redirect('home') 
        else:
            context_error['error_message'] = "El nombre de usuario ya existe o hubo un error al crear la cuenta."
            return render(request, 'store/register.html', context_error)

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
        user_service = UserService()

        user_service._load_users() 
        
        all_users = user_service._users # Obtener todos los usuarios

        # Obtener el ID del usuario logueado desde la sesión
        logged_in_user_id = request.session.get('user_id')
        
        context = {
            'users': all_users, 
            'titulo': 'Administración de Usuarios',
            # Pasar el ID del admin al template
            'current_user_id': logged_in_user_id
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
    # Forzar la carga de usuarios para ver archivo JSON actualizado
    service = UserService()
    service._load_users()

    user_object = service.get_user_by_username(logged_in_username)
    
    if not user_object:
        request.session.flush() 
        messages.error(request, "Perfil no encontrado. Inicia sesión de nuevo.")
        return redirect('login')
        
    context = {
        'user': user_object, 
        'username': user_object.username,
        'is_admin': user_object.role == 'admin', 
        'email': user_object.email,
        'address': user_object.address,
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
            'branches_json': branches # Se convierte a JSON en el template
        }
        return render(request, self.template_name, context)

class SetBranchView(View):
    """Guarda el ID de la sucursal en la sesión del usuario."""
    def post(self, request):
        branch_id = request.POST.get('branch_id')
        
        if branch_id and branch_id.isdigit():
            request.session['selected_branch_id'] = int(branch_id)
            return JsonResponse({'success': True, 'branch_id': int(branch_id)})
        
        return JsonResponse({'success': False, 'error': 'ID de sucursal inválido'}, status=400)
    
class HomeView(View):
    """
    Vista para renderizar la página de inicio (index.html).
    Incluye la lógica para mostrar el modal de selección de sucursal.
    """
    def get(self, request):
        try: 
        
            # Obtener la sucursal de la sesión
            selected_branch_id = request.session.get('selected_branch_id')
            
            # Obtener TODAS las sucursales para el modal
            branches = branch_service.get_all_branches()

            # Convertir branches a JSON para el template
            branches_json = json.dumps(branches) if branches else '[]'

            context = {
                'branches': branches,
                'branches_json': branches_json,  
                # Esta bandera controla si el JavaScript debe abrir el modal
                'show_branch_modal': selected_branch_id is None, 
                'titulo': 'Inicio'
            }
            
            return render(request, 'store/index.html', context)
                    
        except Exception as e:
            print(f"Error en HomeView: {e}")
            # Contexto de fallback
            context = {
                'branches': [],
                'branches_json': '[]',
                'show_branch_modal': True,
                'titulo': 'Inicio'
            }
            return render(request, 'store/index.html', context)

# --- VISTA PARA LIMPIAR LA SUCURSAL SELECCIONADA ---
class ClearBranchView(View):
    """Vista para limpiar la sucursal seleccionada de la sesión."""
    def get(self, request):
        if 'selected_branch_id' in request.session:
            del request.session['selected_branch_id']
            messages.info(request, "La sucursal seleccionada ha sido borrada de tu sesión.")
        return redirect('home') # Redirige al inicio (donde el modal saltará)



class SetAdminBranchFilterView(AdminRequiredMixin, View):

    """Guarda temporalmente el ID de la sucursal en la sesión del admin y devuelve JSON."""
    
    def post(self, request):
        # Obtener el ID de la sucursal del cuerpo de la solicitud POST
        branch_id_str = request.POST.get('branch_id')
            
        if not branch_id_str or not branch_id_str.isdigit():
            return JsonResponse({'success': False, 'error': 'ID de sucursal inválido'}, status=400)
                
        branch_id = int(branch_id_str)
            
        # Guardamos el filtro en la sesión
        request.session['admin_product_filter_branch_id'] = branch_id
            
        # 3. Respuesta JSON de éxito
        return JsonResponse({'success': True, 'branch_id': branch_id})
        

class ClearAdminBranchFilterView(AdminRequiredMixin, View):
    """Limpia el filtro de sucursal de la sesión del admin."""
    def get(self, request):
        if 'admin_product_filter_branch_id' in request.session:
            del request.session['admin_product_filter_branch_id']
            messages.info(request, "Filtro de sucursal de administración limpiado.")
        return redirect('admin-product-view')