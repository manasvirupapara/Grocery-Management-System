"""
Batch Management Utilities
Helper functions for FIFO stock management
"""

from django.utils import timezone
from store.models import Batch, Product


def process_order_with_fifo(order_items):
    """
    Process order items and deduct stock using FIFO method.
    
    Args:
        order_items: List of dicts with 'product_id' and 'quantity'
        Example: [
            {'product_id': 1, 'quantity': 10},
            {'product_id': 2, 'quantity': 5}
        ]
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'failed_products': list (if any)
        }
    """
    failed_products = []
    
    for item in order_items:
        try:
            product = Product.objects.get(id=item['product_id'])
            quantity = item['quantity']
            
            # Deduct stock using FIFO
            success = Batch.deduct_stock_fifo(product, quantity)
            
            if not success:
                failed_products.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'requested': quantity,
                    'available': Batch.get_total_stock(product)
                })
        
        except Product.DoesNotExist:
            failed_products.append({
                'product_id': item['product_id'],
                'product_name': 'Unknown',
                'error': 'Product not found'
            })
    
    if failed_products:
        return {
            'success': False,
            'message': 'Insufficient stock for some products',
            'failed_products': failed_products
        }
    
    return {
        'success': True,
        'message': 'Stock deducted successfully',
        'failed_products': []
    }


def get_product_stock_info(product):
    """
    Get detailed stock information for a product.
    
    Args:
        product: Product instance
    
    Returns:
        dict: {
            'total_stock': int,
            'available_batches': int,
            'expired_batches': int,
            'expiring_soon': int (within 7 days),
            'oldest_batch_date': date or None,
            'newest_batch_date': date or None
        }
    """
    all_batches = product.batches.all()
    available_batches = [b for b in all_batches if b.is_available()]
    expired_batches = [b for b in all_batches if b.is_expired()]
    
    # Batches expiring within 7 days
    expiring_soon = [
        b for b in available_batches 
        if b.days_until_expiry() is not None and 0 <= b.days_until_expiry() <= 7
    ]
    
    return {
        'total_stock': Batch.get_total_stock(product),
        'available_batches': len(available_batches),
        'expired_batches': len(expired_batches),
        'expiring_soon': len(expiring_soon),
        'oldest_batch_date': available_batches[0].manufacturing_date if available_batches else None,
        'newest_batch_date': available_batches[-1].manufacturing_date if available_batches else None
    }


def check_stock_availability(product_id, quantity):
    """
    Check if sufficient stock is available for a product.
    
    Args:
        product_id: Product ID
        quantity: Required quantity
    
    Returns:
        dict: {
            'available': bool,
            'total_stock': int,
            'requested': int
        }
    """
    try:
        product = Product.objects.get(id=product_id)
        total_stock = Batch.get_total_stock(product)
        
        return {
            'available': total_stock >= quantity,
            'total_stock': total_stock,
            'requested': quantity
        }
    except Product.DoesNotExist:
        return {
            'available': False,
            'total_stock': 0,
            'requested': quantity,
            'error': 'Product not found'
        }


def get_expiring_batches(days=7):
    """
    Get all batches expiring within specified days.
    
    Args:
        days: Number of days (default: 7)
    
    Returns:
        QuerySet of Batch objects
    """
    from datetime import timedelta
    
    expiry_threshold = timezone.now().date() + timedelta(days=days)
    
    return Batch.objects.filter(
        quantity__gt=0,
        expiry_date__lte=expiry_threshold,
        expiry_date__gte=timezone.now().date()
    ).order_by('expiry_date')


def get_expired_batches():
    """
    Get all expired batches with remaining stock.
    
    Returns:
        QuerySet of Batch objects
    """
    return Batch.objects.filter(
        quantity__gt=0,
        expiry_date__lt=timezone.now().date()
    ).order_by('expiry_date')


def cleanup_zero_stock_batches(product=None):
    """
    Delete batches with zero stock (optional cleanup).
    
    Args:
        product: Product instance (optional). If None, cleans all products.
    
    Returns:
        int: Number of batches deleted
    """
    if product:
        deleted = product.batches.filter(quantity=0).delete()
    else:
        deleted = Batch.objects.filter(quantity=0).delete()
    
    return deleted[0] if deleted else 0


def add_stock_to_product(product_id, batch_number, manufacturing_date, expiry_date, quantity, cost_price=None):
    """
    Add a new batch to a product.
    
    Args:
        product_id: Product ID
        batch_number: Unique batch number
        manufacturing_date: Manufacturing date (YYYY-MM-DD or date object)
        expiry_date: Expiry date (YYYY-MM-DD or date object)
        quantity: Quantity to add
        cost_price: Cost price per unit (optional)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'batch': Batch instance (if successful)
        }
    """
    try:
        product = Product.objects.get(id=product_id)
        
        # Check if batch number already exists
        if Batch.objects.filter(batch_number=batch_number).exists():
            return {
                'success': False,
                'message': f'Batch number {batch_number} already exists',
                'batch': None
            }
        
        # Create batch
        batch = Batch.objects.create(
            product=product,
            batch_number=batch_number,
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            quantity=quantity,
            cost_price=cost_price
        )
        
        # Update product stock
        product.stock_quantity = Batch.get_total_stock(product)
        product.save()
        
        return {
            'success': True,
            'message': f'Batch {batch_number} added successfully',
            'batch': batch
        }
    
    except Product.DoesNotExist:
        return {
            'success': False,
            'message': 'Product not found',
            'batch': None
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e),
            'batch': None
        }


# Example Usage:
"""
# 1. Process order with FIFO
order_items = [
    {'product_id': 1, 'quantity': 10},
    {'product_id': 2, 'quantity': 5}
]
result = process_order_with_fifo(order_items)
print(result)

# 2. Check stock availability
availability = check_stock_availability(product_id=1, quantity=50)
print(availability)

# 3. Get product stock info
product = Product.objects.get(id=1)
info = get_product_stock_info(product)
print(info)

# 4. Get expiring batches
expiring = get_expiring_batches(days=7)
for batch in expiring:
    print(f"{batch.batch_number} expires in {batch.days_until_expiry()} days")

# 5. Add new batch
result = add_stock_to_product(
    product_id=1,
    batch_number="BATCH-003",
    manufacturing_date="2024-03-01",
    expiry_date="2025-03-01",
    quantity=200,
    cost_price=60.00
)
print(result)
"""
