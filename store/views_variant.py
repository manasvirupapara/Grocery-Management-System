"""
Views for Product Variant System
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Product, ProductVariant
import json


def product_list(request):
    """
    Display list of all active products
    """
    products = Product.objects.filter(is_active=True).prefetch_related('variants')
    
    context = {
        'products': products
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, product_id):
    """
    Display product detail page with variant selection
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    variants = product.variants.filter(is_active=True).order_by('price')
    
    # Get default variant (first one or cheapest)
    default_variant = variants.first()
    
    context = {
        'product': product,
        'variants': variants,
        'default_variant': default_variant,
    }
    return render(request, 'store/product_detail.html', context)


@require_http_methods(["GET"])
def get_variant_details(request, variant_id):
    """
    API endpoint to get variant details (price, stock, status)
    Used for dynamic updates when user changes weight selection
    """
    try:
        variant = ProductVariant.objects.get(id=variant_id, is_active=True)
        
        return JsonResponse({
            'success': True,
            'variant': {
                'id': variant.id,
                'weight': variant.weight,
                'price': float(variant.price),
                'stock': variant.stock,
                'status': variant.status,
                'status_display': variant.get_status_display(),
                'is_in_stock': variant.is_in_stock(),
                'is_low_stock': variant.is_low_stock(),
                'is_out_of_stock': variant.is_out_of_stock(),
            }
        })
    except ProductVariant.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Variant not found'
        }, status=404)


@require_http_methods(["POST"])
def add_variant_to_cart(request):
    """
    Add product variant to cart
    """
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))
        
        variant = ProductVariant.objects.get(id=variant_id, is_active=True)
        
        # Check stock availability
        if variant.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {variant.stock} items available'
            }, status=400)
        
        # Decrease stock
        variant.decrease_stock(quantity)
        
        return JsonResponse({
            'success': True,
            'message': 'Added to cart',
            'variant': {
                'id': variant.id,
                'product_name': variant.product.name,
                'weight': variant.weight,
                'price': float(variant.price),
                'quantity': quantity,
                'remaining_stock': variant.stock,
                'status': variant.status
            }
        })
        
    except ProductVariant.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Variant not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def category_products(request, category_id):
    """
    Display products filtered by category
    """
    from .models import Category
    
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(
        category=category, 
        is_active=True
    ).prefetch_related('variants')
    
    context = {
        'category': category,
        'products': products
    }
    return render(request, 'store/category_products.html', context)


def search_products(request):
    """
    Search products by name or description
    """
    query = request.GET.get('q', '')
    
    if query:
        products = Product.objects.filter(
            is_active=True
        ).filter(
            models.Q(name__icontains=query) | 
            models.Q(description__icontains=query)
        ).prefetch_related('variants')
    else:
        products = Product.objects.none()
    
    context = {
        'products': products,
        'query': query
    }
    return render(request, 'store/search_results.html', context)
