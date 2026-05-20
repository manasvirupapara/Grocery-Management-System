"""
API Views for Store - Cart and Inventory Management
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Product
import json


@csrf_exempt
@require_http_methods(["POST"])
def add_to_cart_api(request):
    """
    Add product to cart and decrease stock in database using FIFO batch system
    """
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id:
            return JsonResponse({
                'success': False,
                'message': 'Product ID is required'
            }, status=400)
        
        # Get product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            }, status=404)
        
        # Check if product is active
        if not product.is_active:
            return JsonResponse({
                'success': False,
                'message': 'Product is not available'
            }, status=400)
        
        # Check if product has batches
        from .models import Batch
        has_batches = product.batches.exists()
        
        if has_batches:
            # Use FIFO batch system
            success = Batch.deduct_stock_fifo(product, quantity)
            
            if not success:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {product.stock_quantity} units available',
                    'available_stock': product.stock_quantity
                }, status=400)
        else:
            # Direct stock deduction for products without batches
            with transaction.atomic():
                product = Product.objects.select_for_update().get(id=product_id)
                
                # Check stock availability
                if product.stock_quantity < quantity:
                    return JsonResponse({
                        'success': False,
                        'message': f'Only {product.stock_quantity} units available',
                        'available_stock': product.stock_quantity
                    }, status=400)
                
                # Decrease stock
                product.stock_quantity -= quantity
                product.save(update_fields=['stock_quantity'])
        
        # Refresh product to get updated stock
        product.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart',
            'product_id': product.id,
            'product_name': product.name,
            'category_name': product.category.name if product.category else '',
            'remaining_stock': product.stock_quantity,
            'is_low_stock': product.stock_quantity <= product.low_stock_threshold,
            'is_out_of_stock': product.stock_quantity == 0
        })
            
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def remove_from_cart_api(request):
    """
    Remove product from cart and increase stock in database
    """
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id:
            return JsonResponse({
                'success': False,
                'message': 'Product ID is required'
            }, status=400)
        
        # Get product and update stock atomically
        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=product_id)
            
            # Increase stock back
            product.stock_quantity += quantity
            product.save(update_fields=['stock_quantity'])
            
            return JsonResponse({
                'success': True,
                'message': 'Product removed from cart',
                'product_id': product.id,
                'category_name': product.category.name if product.category else '',
                'remaining_stock': product.stock_quantity,
                'is_low_stock': product.stock_quantity <= product.low_stock_threshold,
                'is_out_of_stock': product.stock_quantity == 0
            })
            
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_cart_quantity_api(request):
    """
    Update cart quantity and adjust stock accordingly
    """
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        old_quantity = int(data.get('old_quantity', 0))
        new_quantity = int(data.get('new_quantity', 1))
        
        if not product_id:
            return JsonResponse({
                'success': False,
                'message': 'Product ID is required'
            }, status=400)
        
        quantity_diff = new_quantity - old_quantity
        
        # Get product and update stock atomically
        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=product_id)
            
            if quantity_diff > 0:
                # Increasing quantity - check stock
                if product.stock_quantity < quantity_diff:
                    return JsonResponse({
                        'success': False,
                        'message': f'Only {product.stock_quantity} more units available',
                        'available_stock': product.stock_quantity
                    }, status=400)
                product.stock_quantity -= quantity_diff
            else:
                # Decreasing quantity - return stock
                product.stock_quantity += abs(quantity_diff)
            
            product.save(update_fields=['stock_quantity'])
            
            return JsonResponse({
                'success': True,
                'message': 'Cart updated',
                'product_id': product.id,
                'remaining_stock': product.stock_quantity,
                'is_low_stock': product.stock_quantity <= product.low_stock_threshold,
                'is_out_of_stock': product.stock_quantity == 0
            })
            
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_product_stock(request, product_id):
    """
    Get current stock for a product
    """
    try:
        product = Product.objects.get(id=product_id)
        
        return JsonResponse({
            'success': True,
            'product_id': product.id,
            'product_name': product.name,
            'stock_quantity': product.stock_quantity,
            'is_low_stock': product.stock_quantity <= product.low_stock_threshold,
            'is_out_of_stock': product.stock_quantity == 0,
            'is_active': product.is_active
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_order_api(request):
    """
    Create order from checkout page
    """
    try:
        data = json.loads(request.body)
        print(f"[DEBUG] Received order data: {data.keys()}")
        
        # Extract order data
        full_name = data.get('fullName', '').strip()
        mobile = data.get('mobile', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        city = data.get('city', '').strip()
        pincode = data.get('pincode', '').strip()
        landmark = data.get('landmark', '').strip()
        
        payment_method = data.get('paymentMethod', 'COD').upper()
        cart_items = data.get('cart', [])
        subtotal = float(data.get('subtotal', 0))
        tax = float(data.get('tax', 0))
        delivery_fee = float(data.get('deliveryFee', 0))
        total = float(data.get('total', 0))
        
        print(f"[DEBUG] Customer: {full_name}, Mobile: {mobile}, Items: {len(cart_items)}")
        
        # Validation
        if not all([full_name, mobile, address, city, pincode]):
            print("[DEBUG] Validation failed: Missing required fields")
            return JsonResponse({
                'success': False,
                'message': 'All required fields must be filled'
            }, status=400)
        
        if not cart_items:
            print("[DEBUG] Validation failed: Cart is empty")
            return JsonResponse({
                'success': False,
                'message': 'Cart is empty'
            }, status=400)
        
        # Create or get customer
        from customers.models import Customer
        from .models import Order, OrderItem
        import uuid
        from datetime import datetime
        
        with transaction.atomic():
            # Try to find existing customer by phone
            customer, created = Customer.objects.get_or_create(
                phone=mobile,
                defaults={
                    'name': full_name,
                    'email': email if email else f"{mobile}@customer.com",
                    'location': f"{city} - {pincode}",
                    'gender': 'Male'  # Default value
                }
            )
            print(f"[DEBUG] Customer {'created' if created else 'found'}: {customer.name}")
            
            # Update customer info if exists
            if not created:
                customer.name = full_name
                if email:
                    customer.email = email
                customer.location = f"{city} - {pincode}"
                customer.save()
                print(f"[DEBUG] Customer updated")
            
            # Generate order ID (without # symbol for URL compatibility)
            order_id = f"TDG{datetime.now().strftime('%Y%m%d%H%M%S')}"
            print(f"[DEBUG] Generated order ID: {order_id}")
            
            # Map payment method
            payment_method_map = {
                'COD': 'COD',
                'UPI': 'UPI',
                'CARD': 'Card',
                'NETBANKING': 'NetBanking'
            }
            payment_method_db = payment_method_map.get(payment_method, 'COD')
            
            # Create order
            order = Order.objects.create(
                order_id=order_id,
                customer=customer,
                payment_method=payment_method_db,
                payment_status='Pending' if payment_method_db == 'COD' else 'Success',
                total_amount=total,
                delivery_status='Order_Placed'
            )
            print(f"[DEBUG] Order created: {order.order_id}, PK: {order.pk}")
            
            # Create order items
            for idx, item in enumerate(cart_items):
                product_id = item.get('id')
                product_name = item.get('name', 'Unknown Product')
                quantity = int(item.get('qty', item.get('quantity', 1)))
                price = float(item.get('price', 0))
                
                # Try to link to product if ID exists
                product_obj = None
                cost_price = 0
                if product_id:
                    try:
                        product_obj = Product.objects.get(id=product_id)
                        cost_price = float(product_obj.cost_price)
                    except Product.DoesNotExist:
                        pass
                
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product_obj,
                    product_name=product_name,
                    quantity=quantity,
                    price=price,
                    cost_price=cost_price
                )
                print(f"[DEBUG] Order item {idx+1} created: {product_name} x {quantity}")
            
            # Update order totals
            order.update_totals()
            print(f"[DEBUG] Order totals updated: {order.total_amount}")
            
            # Create Invoice automatically
            from .models import Invoice, InvoiceItem, Tax
            
            # Get active tax
            active_tax = Tax.get_active()
            print(f"[DEBUG] Active tax: {active_tax}")
            
            # Create invoice
            invoice = Invoice.objects.create(
                order=order,
                customer=customer,
                tax=active_tax,
                subtotal=subtotal,
                discount=0,
                payment_status='Pending' if payment_method_db == 'COD' else 'Paid'
            )
            print(f"[DEBUG] Invoice created: {invoice.invoice_number}")
            
            # Create invoice items from order items
            for order_item in order.items.all():
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product_name=order_item.product_name,
                    quantity=order_item.quantity,
                    unit_price=order_item.price
                )
            print(f"[DEBUG] Invoice items created: {invoice.items.count()}")
            
            # Recalculate invoice totals (this will apply tax)
            invoice.recalculate(save=True)
            print(f"[DEBUG] Invoice totals calculated: {invoice.total_amount}")
            
            print(f"[DEBUG] Order creation successful!")
            
            return JsonResponse({
                'success': True,
                'message': 'Order placed successfully',
                'order_id': order.order_id,
                'order_pk': order.pk,
                'invoice_number': invoice.invoice_number,
                'customer_name': customer.name,
                'total_amount': float(order.total_amount)
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[DEBUG] Error creating order: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error creating order: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_invoice_api(request, order_id):
    """
    Get invoice data by order ID
    """
    try:
        from .models import Order, Invoice
        
        print(f"[DEBUG] Looking for order with ID: {order_id}")
        
        # Get order
        try:
            order = Order.objects.get(order_id=order_id)
            print(f"[DEBUG] Order found: {order.order_id}, Customer: {order.customer.name}")
        except Order.DoesNotExist:
            print(f"[DEBUG] Order not found with ID: {order_id}")
            # Try to list all orders for debugging
            all_orders = Order.objects.all()[:5]
            print(f"[DEBUG] Available orders: {[o.order_id for o in all_orders]}")
            return JsonResponse({
                'success': False,
                'message': f'Order not found with ID: {order_id}'
            }, status=404)
        
        # Get or create invoice
        try:
            invoice = Invoice.objects.get(order=order)
            print(f"[DEBUG] Invoice found: {invoice.invoice_number}")
        except Invoice.DoesNotExist:
            print(f"[DEBUG] Invoice not found for order {order_id}, creating one...")
            # Create invoice if it doesn't exist
            from .models import Tax, InvoiceItem
            
            active_tax = Tax.get_active()
            
            invoice = Invoice.objects.create(
                order=order,
                customer=order.customer,
                tax=active_tax,
                subtotal=order.total_amount,
                discount=0,
                payment_status='Pending' if order.payment_method == 'COD' else 'Paid'
            )
            
            # Create invoice items from order items
            for order_item in order.items.all():
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product_name=order_item.product_name,
                    quantity=order_item.quantity,
                    unit_price=order_item.price
                )
            
            # Recalculate invoice totals
            invoice.recalculate(save=True)
            print(f"[DEBUG] Invoice created: {invoice.invoice_number}")
        
        # Get invoice items
        invoice_items = []
        for item in invoice.items.all():
            invoice_items.append({
                'product_name': item.product_name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'line_total': float(item.line_total)
            })
        
        print(f"[DEBUG] Returning invoice data with {len(invoice_items)} items")
        
        # Prepare response
        return JsonResponse({
            'success': True,
            'invoice': {
                'invoice_number': invoice.invoice_number,
                'order_id': order.order_id,
                'issue_date': invoice.issue_date.strftime('%Y-%m-%d'),
                'customer_name': order.customer.name,
                'customer_phone': order.customer.phone,
                'customer_email': order.customer.email,
                'customer_location': order.customer.location,
                'items': invoice_items,
                'subtotal': float(invoice.subtotal),
                'discount': float(invoice.discount),
                'tax_name': invoice.tax_name,
                'tax_percentage': float(invoice.tax_percentage),
                'tax_amount': float(invoice.tax_amount),
                'total_amount': float(invoice.total_amount),
                'payment_method': order.payment_method,
                'payment_status': invoice.payment_status,
                'transaction_id': invoice.transaction_id or order.transaction_id,
                'delivery_status': order.delivery_status
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[DEBUG] Error in get_invoice_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error fetching invoice: {str(e)}'
        }, status=500)



@require_http_methods(["GET"])
def get_product_with_variants(request, product_id):
    """
    Get product details with all variants (stock from batches)
    """
    try:
        from .models import ProductVariant, Batch
        from django.db.models import Sum
        
        product = Product.objects.get(id=product_id, is_active=True)
        
        # Get all active variants for this product
        variants = ProductVariant.objects.filter(
            product=product,
            is_active=True
        ).order_by('price')
        
        # Get gallery images
        gallery_images = list(product.images.all().values_list('image', flat=True))
        
        # Prepare variants data with stock from batches
        variants_data = []
        for variant in variants:
            # Get total stock from all batches for this product
            # (Batches are linked to Product, not ProductVariant)
            batches = Batch.objects.filter(
                product=product,
                quantity__gt=0
            ).order_by('expiry_date')
            
            # Calculate total stock from all batches
            total_stock = batches.aggregate(total=Sum('quantity'))['total'] or 0
            
            # Get earliest expiry date from available batches
            earliest_batch = batches.first()
            expiry_date = earliest_batch.expiry_date if earliest_batch else None
            
            variants_data.append({
                'id': variant.id,
                'weight': variant.weight,
                'unit_type': variant.unit_type,
                'price': float(variant.price),
                'stock': total_stock,  # From batches
                'low_stock_alert': 10,
                'expiry_date': expiry_date.strftime('%d %b, %Y') if expiry_date else None,
                'is_in_stock': total_stock > 0,
                'is_low_stock': 0 < total_stock <= 10,
                'discount_percentage': 0  # Add discount logic if needed
            })
        
        # Calculate total stock from all batches
        total_product_stock = Batch.objects.filter(
            product=product,
            quantity__gt=0
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Apply active offers to get final price
        from django.utils import timezone as tz
        from .models import Offer
        today = tz.now().date()
        valid_offers = Offer.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).prefetch_related('products', 'categories')
        
        final_price = float(product.selling_price)
        original_price = float(product.selling_price)
        discount_pct = 0
        
        for offer in valid_offers:
            applies = offer.products.filter(id=product.id).exists()
            if not applies and product.category:
                applies = offer.categories.filter(id=product.category.id).exists()
            if applies:
                if offer.discount_type == 'percentage':
                    d = float(offer.discount_value)
                    if d > discount_pct:
                        discount_pct = d
                        final_price = original_price - (original_price * d / 100)
                elif offer.discount_type == 'fixed':
                    d_pct = (float(offer.discount_value) / original_price) * 100
                    if d_pct > discount_pct:
                        discount_pct = d_pct
                        final_price = original_price - float(offer.discount_value)
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description or 'High quality product with premium ingredients.',
                'category_name': product.category.name if product.category else 'Product',
                'image': product.image.url if product.image else '',
                'gallery_images': [request.build_absolute_uri(img) for img in gallery_images],
                'final_price': round(final_price, 2),
                'original_price': original_price,
                'discount_percentage': round(discount_pct, 2),
                'stock_quantity': total_product_stock,
                'variants': variants_data
            }
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
