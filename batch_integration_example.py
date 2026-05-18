"""
Example Integration of Batch Management with Order Processing
This file shows how to integrate FIFO batch management into your views.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from store.models import Product, Batch, Order, OrderItem
from batch_utils import process_order_with_fifo, check_stock_availability, get_product_stock_info


# ============================================
# EXAMPLE 1: Product List View (Customer Side)
# ============================================
def product_list_view(request):
    """
    Display products with available stock (hides batch details from customers).
    """
    products = Product.objects.filter(is_active=True)
    
    # Add available stock to each product
    for product in products:
        # Get total available stock (excludes expired batches)
        product.available_stock = Batch.get_total_stock(product)
        
        # Determine stock status
        if product.available_stock == 0:
            product.stock_status = "OUT OF STOCK"
            product.stock_class = "out-of-stock"
        elif product.available_stock <= product.low_stock_threshold:
            product.stock_status = f"LOW STOCK ({product.available_stock} left)"
            product.stock_class = "low-stock"
        else:
            product.stock_status = f"IN STOCK ({product.available_stock} available)"
            product.stock_class = "in-stock"
    
    return render(request, 'store/shop.html', {
        'products': products
    })


# ============================================
# EXAMPLE 2: Check Stock Before Adding to Cart
# ============================================
@require_http_methods(["POST"])
def check_stock_api(request):
    """
    API endpoint to check stock availability before adding to cart.
    """
    import json
    
    data = json.loads(request.body)
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    result = check_stock_availability(product_id, quantity)
    
    return JsonResponse(result)


# ============================================
# EXAMPLE 3: Create Order with FIFO Stock Deduction
# ============================================
@require_http_methods(["POST"])
@transaction.atomic
def create_order_view(request):
    """
    Create order and deduct stock using FIFO method.
    """
    import json
    
    data = json.loads(request.body)
    customer_id = data.get('customer_id')
    cart_items = data.get('cart_items')  # [{'product_id': 1, 'quantity': 10}, ...]
    
    # Validate stock availability first
    for item in cart_items:
        availability = check_stock_availability(item['product_id'], item['quantity'])
        if not availability['available']:
            return JsonResponse({
                'success': False,
                'message': f'Insufficient stock for product ID {item["product_id"]}',
                'available_stock': availability['total_stock'],
                'requested': availability['requested']
            })
    
    # Create order
    order = Order.objects.create(
        customer_id=customer_id,
        order_id=f"ORD-{Order.objects.count() + 1:06d}",
        payment_status="Pending",
        payment_method="COD"
    )
    
    # Process items with FIFO stock deduction
    total_amount = 0
    
    for item in cart_items:
        product = Product.objects.get(id=item['product_id'])
        quantity = item['quantity']
        
        # Deduct stock using FIFO
        success = Batch.deduct_stock_fifo(product, quantity)
        
        if not success:
            # Rollback transaction
            transaction.set_rollback(True)
            return JsonResponse({
                'success': False,
                'message': f'Failed to deduct stock for {product.name}'
            })
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.selling_price
        )
        
        total_amount += product.selling_price * quantity
    
    # Update order total
    order.total_amount = total_amount
    order.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Order created successfully',
        'order_id': order.order_id,
        'total_amount': float(total_amount)
    })


# ============================================
# EXAMPLE 4: Product Detail View with Stock Info
# ============================================
def product_detail_view(request, product_id):
    """
    Display product details with stock information.
    """
    product = Product.objects.get(id=product_id)
    
    # Get stock info (for admin/internal use)
    stock_info = get_product_stock_info(product)
    
    # For customer view, only show total available stock
    product.available_stock = stock_info['total_stock']
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'stock_info': stock_info  # Optional: for admin view
    })


# ============================================
# EXAMPLE 5: Admin Dashboard - Expiring Batches Alert
# ============================================
def admin_dashboard_view(request):
    """
    Admin dashboard showing expiring batches.
    """
    from batch_utils import get_expiring_batches, get_expired_batches
    
    # Get batches expiring within 7 days
    expiring_soon = get_expiring_batches(days=7)
    
    # Get expired batches with remaining stock
    expired_batches = get_expired_batches()
    
    return render(request, 'admin/dashboard.html', {
        'expiring_soon': expiring_soon,
        'expired_batches': expired_batches
    })


# ============================================
# EXAMPLE 6: AJAX Stock Check (Real-time)
# ============================================
@require_http_methods(["GET"])
def get_product_stock(request, product_id):
    """
    Get real-time stock for a product (AJAX endpoint).
    """
    try:
        product = Product.objects.get(id=product_id)
        available_stock = Batch.get_total_stock(product)
        
        return JsonResponse({
            'success': True,
            'product_id': product_id,
            'product_name': product.name,
            'available_stock': available_stock,
            'in_stock': available_stock > 0
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        })


# ============================================
# EXAMPLE 7: Bulk Order Processing
# ============================================
@require_http_methods(["POST"])
@transaction.atomic
def process_bulk_order(request):
    """
    Process multiple orders at once with FIFO stock deduction.
    """
    import json
    
    data = json.loads(request.body)
    orders = data.get('orders')  # List of order objects
    
    results = []
    
    for order_data in orders:
        cart_items = order_data.get('cart_items')
        
        # Process order with FIFO
        result = process_order_with_fifo(cart_items)
        
        if result['success']:
            # Create order record
            order = Order.objects.create(
                customer_id=order_data.get('customer_id'),
                order_id=f"ORD-{Order.objects.count() + 1:06d}",
                payment_status="Pending"
            )
            
            results.append({
                'order_id': order.order_id,
                'success': True
            })
        else:
            results.append({
                'customer_id': order_data.get('customer_id'),
                'success': False,
                'failed_products': result['failed_products']
            })
    
    return JsonResponse({
        'success': True,
        'results': results
    })


# ============================================
# URL Configuration Example
# ============================================
"""
Add these to your urls.py:

from django.urls import path
from . import batch_integration_example as batch_views

urlpatterns = [
    # Customer-facing views
    path('products/', batch_views.product_list_view, name='product_list'),
    path('product/<int:product_id>/', batch_views.product_detail_view, name='product_detail'),
    
    # API endpoints
    path('api/check-stock/', batch_views.check_stock_api, name='check_stock'),
    path('api/create-order/', batch_views.create_order_view, name='create_order'),
    path('api/product-stock/<int:product_id>/', batch_views.get_product_stock, name='get_product_stock'),
    
    # Admin views
    path('admin/dashboard/', batch_views.admin_dashboard_view, name='admin_dashboard'),
]
"""


# ============================================
# JavaScript Integration Example (Frontend)
# ============================================
"""
// Check stock before adding to cart
async function addToCart(productId, quantity) {
    const response = await fetch('/api/check-stock/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    });
    
    const result = await response.json();
    
    if (result.available) {
        // Add to cart
        let cart = JSON.parse(localStorage.getItem('radhi-cart')) || [];
        cart.push({
            id: productId,
            quantity: quantity
        });
        localStorage.setItem('radhi-cart', JSON.stringify(cart));
        alert('✅ Added to cart!');
    } else {
        alert(`❌ Only ${result.total_stock} units available!`);
    }
}

// Create order with FIFO stock deduction
async function checkout() {
    const cart = JSON.parse(localStorage.getItem('radhi-cart')) || [];
    
    const response = await fetch('/api/create-order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            customer_id: 1,
            cart_items: cart
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        alert(`✅ Order created! Order ID: ${result.order_id}`);
        localStorage.removeItem('radhi-cart');
        window.location.href = '/orders/';
    } else {
        alert(`❌ ${result.message}`);
    }
}
"""
