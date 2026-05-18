"""
Batch Management Views
Custom views for managing batches in the admin panel
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from store.models import Batch, Product, Category
from datetime import date


def batch_list(request):
    """List all batches with search and filter"""
    batches = Batch.objects.all().select_related('product', 'product__category')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        batches = batches.filter(
            Q(batch_number__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )
    
    # Filter by category
    selected_category = request.GET.get('category', '')
    if selected_category:
        batches = batches.filter(product__category_id=selected_category)
    
    # Order by FIFO
    batches = batches.order_by('manufacturing_date', 'created_at')
    
    # Get categories for filter
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'batches': batches,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
    }
    
    return render(request, 'batch_list.html', context)


def batch_add(request):
    """Add new batch"""
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product')
            batch_number = request.POST.get('batch_number')
            manufacturing_date = request.POST.get('manufacturing_date')
            expiry_date = request.POST.get('expiry_date')
            quantity = request.POST.get('quantity')
            cost_price = request.POST.get('cost_price')
            
            # Validate
            if not all([product_id, batch_number, manufacturing_date, expiry_date, quantity]):
                messages.error(request, 'Please fill all required fields')
                return redirect('batch_add')
            
            # Check if batch number already exists
            if Batch.objects.filter(batch_number=batch_number).exists():
                messages.error(request, f'Batch number {batch_number} already exists')
                return redirect('batch_add')
            
            # Create batch
            product = Product.objects.get(id=product_id)
            batch = Batch.objects.create(
                product=product,
                batch_number=batch_number,
                manufacturing_date=manufacturing_date,
                expiry_date=expiry_date,
                quantity=int(quantity),
                cost_price=float(cost_price) if cost_price else None
            )
            
            # Update product stock
            product.stock_quantity = Batch.get_total_stock(product)
            product.save()
            
            messages.success(request, f'Batch {batch_number} created successfully!')
            return redirect('batch_list')
            
        except Exception as e:
            messages.error(request, f'Error creating batch: {str(e)}')
            return redirect('batch_add')
    
    # GET request
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'products': products,
    }
    
    return render(request, 'batch_form.html', context)


def batch_edit(request, batch_id):
    """Edit existing batch"""
    batch = get_object_or_404(Batch, id=batch_id)
    
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product')
            batch_number = request.POST.get('batch_number')
            manufacturing_date = request.POST.get('manufacturing_date')
            expiry_date = request.POST.get('expiry_date')
            quantity = request.POST.get('quantity')
            cost_price = request.POST.get('cost_price')
            
            # Validate
            if not all([product_id, batch_number, manufacturing_date, expiry_date, quantity]):
                messages.error(request, 'Please fill all required fields')
                return redirect('batch_edit', batch_id=batch_id)
            
            # Check if batch number already exists (excluding current batch)
            if Batch.objects.filter(batch_number=batch_number).exclude(id=batch_id).exists():
                messages.error(request, f'Batch number {batch_number} already exists')
                return redirect('batch_edit', batch_id=batch_id)
            
            # Update batch
            old_product = batch.product
            batch.product = Product.objects.get(id=product_id)
            batch.batch_number = batch_number
            batch.manufacturing_date = manufacturing_date
            batch.expiry_date = expiry_date
            batch.quantity = int(quantity)
            batch.cost_price = float(cost_price) if cost_price else None
            batch.save()
            
            # Update product stock for both old and new product
            old_product.stock_quantity = Batch.get_total_stock(old_product)
            old_product.save()
            
            if batch.product.id != old_product.id:
                batch.product.stock_quantity = Batch.get_total_stock(batch.product)
                batch.product.save()
            
            messages.success(request, f'Batch {batch_number} updated successfully!')
            return redirect('batch_list')
            
        except Exception as e:
            messages.error(request, f'Error updating batch: {str(e)}')
            return redirect('batch_edit', batch_id=batch_id)
    
    # GET request
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'batch': batch,
        'products': products,
    }
    
    return render(request, 'batch_form.html', context)


def batch_delete(request, batch_id):
    """Delete batch"""
    batch = get_object_or_404(Batch, id=batch_id)
    
    try:
        product = batch.product
        batch_number = batch.batch_number
        batch.delete()
        
        # Update product stock
        product.stock_quantity = Batch.get_total_stock(product)
        product.save()
        
        messages.success(request, f'Batch {batch_number} deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting batch: {str(e)}')
    
    return redirect('batch_list')
