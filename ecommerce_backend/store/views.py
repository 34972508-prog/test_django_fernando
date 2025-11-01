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

# Se usan default_storage para el manejo de archivos local o en la nube (S3)
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
        all_products = service.get_all_products()

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
    def get(self, request, pk=None):
        service = ProductService()

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
            'pk': pk
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
            
            # 🛑 CORRECCIÓN: Se elimina el 'return redirect' de éxito que interrumpía la creación/actualización.
            
        # Validaciones básicas
        if not title or not price or not stock:
            error_msg = "Título, precio y stock son campos obligatorios"
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

class DeleteProductHTMLView(View):
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
    Vista para listar productos en HTML
    Responde a la URL: /products/list
    """
    def get(self, request):
        service = ProductService()
        productos = service.get_all_products()
        
        # 🛑 CORRECCIÓN: Se elimina el bloque de normalización.
        # Ahora se confía en que 'image_url' devuelto por el service es la ruta/URL correcta.
        
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

        # 🛑 CORRECCIÓN: Se elimina el bloque de normalización.
        # Ahora se confía en que 'image_url' devuelto por el service es la ruta/URL correcta.
        
        context = {
            'producto': product,
            'titulo': product.get('title', 'Detalle del producto')
        }
        return render(request, 'store/product_detail.html', context)