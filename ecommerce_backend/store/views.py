# store/views.py
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .product_service import ProductService
from .decorators import admin_required

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages

from django.core.files.storage import FileSystemStorage
from uuid import uuid4
import os

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile



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
    
class AdminProductView(View):
    def get(self, request):
        service = ProductService()
        # Usamos el service para obtener los datos del JSON
        all_products = service.get_all_products()

        # Pasamos los datos a la plantilla HTML
        context = {
            'products': all_products,
        }
        return render(request, 'store/admin_products.html', context)

class ProductFormView(View):
    """
    Vista dedicada para mostrar el formulario de creación o edición, 
    y manejar el envío (POST) de esos formularios.
    """
    
    #@method_decorator(admin_required)
    def get(self, request, pk=None):  # CAMBIA *args, **kwargs por parámetros explícitos def get(self, request, *args, **kwargs):
        #print("🔍 DEBUG: ProductFormView.get() llamado")
        #print(f"🔍 DEBUG: request.method = {request.method}")
        #print(f"🔍 DEBUG: pk = {pk}")
        #print(f"🔍 DEBUG: URL completa: {request.build_absolute_uri()}")
        service = ProductService()

        product_data = None
        form_title = "Crear Nuevo Producto"

        # Modo Edición (si se pasó una pk)
        if pk is not None:
            #print(f"🔍 DEBUG: Modo EDICIÓN para producto ID: {pk}")
            product_data = service.get_product_by_id(pk)
            #print(f"🔍 DEBUG: Datos del producto: {product_data}")
            if not product_data:
                messages.error(request, "Producto no encontrado")
                return redirect('admin-product-view') # Producto no encontrado
            form_title = f"Editar Producto "
        #else:
            #print("🔍 DEBUG: Modo CREACIÓN de nuevo producto")
        
        # Modo Creación (si pk es None)        
        context = {
            'form_title': form_title,
            'product': product_data, # Los datos se pasan para precargar el formulario
            'is_edit': pk is not None,
            'pk': pk # El ID es necesario para el POST de edición
        }
        #print("🔍 DEBUG: Contexto enviado al template:", context)
        # Renderiza un nuevo template de formulario (lo crearemos en el Paso 3)
        return render(request, 'store/product_form.html', context)

    #@method_decorator(admin_required)
    def post(self, request, pk=None):  # def post(self, request, *args, **kwargs):
        #print("🔍 DEBUG: ProductFormView.post() llamado")
        #print(f"🔍 DEBUG: request.method = {request.method}")
        #print(f"🔍 DEBUG: pk = {pk}")
        #print(f"🔍 DEBUG: Datos POST: {dict(request.POST)}")
        service = ProductService()
        #pk = kwargs.get('pk', None)

        # Obtener datos del formulario
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category_id')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        #image_url = request.POST.get('image_url')
        weight = request.POST.get('weight')

        #print(f"🔍 DEBUG: Datos del formulario:")
        #print(f"  title: {title}")
        #print(f"  description: {description}")
        #print(f"  category_id: {category_id}")
        #print(f"  price: {price}")
        #print(f"  stock: {stock}")
        #print(f"  image_url: {image_url}")
        #print(f"  weight: {weight}")
        # Manejo de la imagen subida
        image_file = request.FILES.get('image')
        image_url = request.POST.get('image_url', '')  # fallback si lo tienes
        if image_file:
            try:
                # Genera un nombre único usando UUID
                file_name = f"productos/{uuid4().hex}{os.path.splitext(image_file.name)[1]}"
                # Guarda el archivo
                path = default_storage.save(file_name, ContentFile(image_file.read()))
                # Obtiene la URL
                image_url = default_storage.url(path)
            except Exception as e:
                messages.error(request, f"Error al subir la imagen: {str(e)}")
            return redirect('product-create' if not pk else 'product-edit', pk=pk)
        """ productos_dir = os.path.join(settings.MEDIA_ROOT, 'productos')
            os.makedirs(productos_dir, exist_ok=True)
            fs = FileSystemStorage(location=productos_dir, base_url=settings.MEDIA_URL + 'productos/')
            ext = os.path.splitext(image_file.name)[1]
            filename = f"{uuid4().hex}{ext}"
            saved_name = fs.save(filename, image_file)
            image_url = fs.base_url + saved_name  # e.g. /media/productos/<file>
"""
        # Validaciones básicas
        if not title or not price or not stock:
            error_msg = "Título, precio y stock son campos obligatorios"
            #print(f"🔍 DEBUG: Error de validación - {error_msg}")
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
                'category_id': int(category_id) if category_id else 1,
                'price': float(price),
                'stock': int(stock),
                'image_url': image_url or '',
                'weight': float(weight) if weight else 0.0,
                'type': 'cake'  # Valor por defecto
            }
        except (ValueError, TypeError) as e:
            error_msg = f"Error en el formato de los datos: {str(e)}"
            #print(f"🔍 DEBUG: Error de conversión - {error_msg}")
            messages.error(request, error_msg)
            if pk:
                return redirect('product-edit', pk=pk)
            else:
                return redirect('product-create')

        # Lógica de creación o edición
        if pk is None:
            #print("🔍 DEBUG: Intentando CREAR producto...")
            new_product = service.create_product(product_data)
            if new_product:
                #print("🔍 DEBUG: ✅ Producto creado exitosamente")
                messages.success(request, "Producto creado exitosamente")
                return redirect('admin-product-view')
            else:
                #print("🔍 DEBUG: ❌ Error al crear producto")
                messages.error(request, "Error al crear el producto")
                return redirect('product-create')
        else:           
            #print(f"🔍 DEBUG: Intentando ACTUALIZAR producto ID: {pk}...")
            updated_product = service.update_product(pk, product_data)
            if updated_product:
                #print("🔍 DEBUG: ✅ Producto actualizado exitosamente")
                messages.success(request, "Producto actualizado exitosamente")
                return redirect('admin-product-view')
            else:
                #print("🔍 DEBUG: ❌ Error al actualizar producto")
                messages.error(request, "Error al actualizar el producto")
                return redirect('product-edit', pk=pk)
class DeleteProductHTMLView(View):
    """
    Vista específica para eliminar productos desde el HTML
    """
    
    def post(self, request, pk):
        #print(f"🔍 DELETE HTML llamado para producto {pk}")
        service = ProductService()
        
        if service.delete_product(pk):
            messages.success(request, f"Producto eliminado exitosamente")
        else:
            messages.error(request, f"Error al eliminar el producto")
        
        return redirect('admin-product-view')
class List_productView(View):
    """
    Vista para listar productos en HTML
    Responde a la URL: /products/list
    """
    def get(self, request):
        service = ProductService()
        productos = service.get_all_products()
        
        #NORMALISA LAS RUTAS DE LAS IMAGENES
        for p in productos:
            img = p.get('image_url') or ''
            if img.startswith('/media/productos/'):
                p['image_url'] = settings.MEDIA_URL + img.split('/media/productos/')[-1]
            elif img and not (img.startswith('http://') or img.startswith('https://') or img.startswith(settings.MEDIA_URL)):
                # opción: si la ruta es relativa, la preparamos con MEDIA_URL
                p['image_url'] = settings.MEDIA_URL + img.lstrip('/')
        
        context = {
            'productos': productos,
            'titulo': 'Catálogo de Productos'
        }
        return render(request, 'store/list_procuct.html', context)
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

        # Normalizar ruta de imagen igual que en el listado
        img = product.get('image_url') or ''
        if img.startswith('/media/productos/'):
            product['image_url'] = settings.MEDIA_URL + img.split('/media/productos/')[-1]
        elif img and not (img.startswith('http://') or img.startswith('https://') or img.startswith(settings.MEDIA_URL)):
            product['image_url'] = settings.MEDIA_URL + img.lstrip('/')

        context = {
            'producto': product,
            'titulo': product.get('title', 'Detalle del producto')
        }
        return render(request, 'store/product_detail.html', context)