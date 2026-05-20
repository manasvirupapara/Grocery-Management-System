import json
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from .models import Category, SubCategory, Offer
from .forms import CategoryForm, SubCategoryForm, OfferForm
from django.db.models import Count
from django.db.models import Sum, F
from .models import Order, OrderItem, Product, ProductImage
from django.core.paginator import Paginator
from customers.models import Customer

# Period filter options (same as dashboard) - "All" first
PERIOD_CHOICES = [
    'All', 'This Year', 'This Month', 'This Week',
    'Last Year', 'Last Month', 'Last Week',
]

def _get_period_date_range(period):
    """Return (start_date, end_date) for the given period string. Uses timezone-aware now."""
    now = timezone.now()
    if not period or period not in PERIOD_CHOICES or period == 'All':
        return None, None  # no filter
    start, end = None, None
    if period == 'This Year':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'This Month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'This Week':
        # Monday as start of week
        weekday = now.weekday()
        start = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == 'Last Year':
        start = now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    elif period == 'Last Month':
        first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start = (first_this_month - timedelta(days=1)).replace(day=1)
        end = first_this_month - timedelta(microseconds=1)
    elif period == 'Last Week':
        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
        start = this_week_start - timedelta(days=7)
        end = this_week_start - timedelta(microseconds=1)
    return start, end


def _get_previous_period_range(period):
    """Get the previous period date range for comparison."""
    now = timezone.now()
    if not period or period == 'All':
        return None, None
    
    if period == 'This Year':
        start = now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    elif period == 'This Month':
        first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start = (first_this_month - timedelta(days=1)).replace(day=1)
        end = first_this_month - timedelta(microseconds=1)
    elif period == 'This Week':
        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
        start = this_week_start - timedelta(days=7)
        end = this_week_start - timedelta(microseconds=1)
    elif period == 'Last Year':
        start = now.replace(year=now.year - 2, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    elif period == 'Last Month':
        first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_last_month = (first_this_month - timedelta(days=1)).replace(day=1)
        start = (first_last_month - timedelta(days=1)).replace(day=1)
        end = first_last_month - timedelta(microseconds=1)
    elif period == 'Last Week':
        weekday = now.weekday()
        this_week_start = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
        last_week_start = this_week_start - timedelta(days=7)
        start = last_week_start - timedelta(days=7)
        end = last_week_start - timedelta(microseconds=1)
    else:
        return None, None
    
    return start, end


def _calculate_percentage_change(current, previous):
    """Calculate percentage change between current and previous values."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')

    return render(request, 'login.html')


def admin_logout(request):
    logout(request)
    return render(request, 'logout.html')


# --------------------
# PRODUCT MANAGEMENT
# --------------------
def product_list(request):
    """Product list with search, filter, and pagination."""
    from django.utils import timezone
    from django.db.models import Sum, Q as DQ

    products = Product.objects.select_related('category', 'subcategory').prefetch_related('batches', 'variants').order_by('-id')

    search = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '').strip()
    subcategory_filter = request.GET.get('subcategory', '').strip()
    status_filter = request.GET.get('status', '').strip()

    # Search by product name or SKU
    if search:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=search) | Q(sku__icontains=search)
        )

    # Filter by category
    if category_filter and category_filter != 'all':
        products = products.filter(category_id=category_filter)

    # Filter by subcategory
    if subcategory_filter and subcategory_filter != 'all':
        products = products.filter(subcategory_id=subcategory_filter)

    # Filter by status
    if status_filter == 'in_stock':
        products = products.filter(stock_quantity__gt=0, is_active=True)
    elif status_filter == 'out_of_stock':
        products = products.filter(stock_quantity=0)
    elif status_filter == 'low_stock':
        products = products.filter(stock_quantity__lte=F('low_stock_threshold'), stock_quantity__gt=0)

    # Pagination
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Har product ke liye active batch stock calculate karo
    today = timezone.now().date()
    for product in page_obj.object_list:
        active_batches = [b for b in product.batches.all() if b.quantity > 0 and b.expiry_date >= today]
        product.active_batch_count = len(active_batches)
        product.active_stock = sum(b.quantity for b in active_batches)

    # Get all categories for filter dropdown (both active and inactive)
    categories = Category.objects.all().order_by('name')
    subcategories = SubCategory.objects.select_related('category').all().order_by('name')

    context = {
        'page_obj': page_obj,
        'search': search,
        'category_filter': category_filter,
        'subcategory_filter': subcategory_filter,
        'status_filter': status_filter,
        'categories': categories,
        'subcategories': subcategories,
    }
    return render(request, 'products/product_list.html', context)


@login_required(login_url='login')
def add_product(request):
    """Add new product."""
    if request.method == 'POST':
        from .forms import ProductForm
        from .models import ProductVariant
        from datetime import datetime
        
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                product = form.save()
                
                # Handle multiple images
                images = request.FILES.getlist('additional_images')
                for idx, image in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image,
                        is_primary=(idx == 0 and not product.image)
                    )
                
                # Handle product variants (weight, price, and optional stock)
                variant_index = 0
                while True:
                    weight = request.POST.get(f'variant_weight_{variant_index}')
                    if not weight:
                        break
                    
                    price = request.POST.get(f'variant_price_{variant_index}')
                    unit_type = request.POST.get(f'variant_unit_type_{variant_index}', 'kg')
                    stock = request.POST.get(f'variant_stock_{variant_index}', '0')
                    
                    if weight and price:
                        # Convert stock to integer, default to 0 if empty
                        try:
                            stock_value = int(stock) if stock else 0
                        except ValueError:
                            stock_value = 0
                        
                        ProductVariant.objects.create(
                            product=product,
                            weight=weight,
                            price=float(price),
                            unit_type=unit_type,
                            stock=stock_value,  # Can be set directly or managed through Batch
                            low_stock_alert=10,
                            is_active=True
                        )
                    
                    variant_index += 1
                
                messages.success(request, f'✓ Product added successfully with {variant_index} variant(s)! You can add batches for expiry tracking or use quick stock.')
                return redirect('product_list')
            except Exception as e:
                # Handle duplicate product error
                form.add_error('name', f'Error: {str(e)}')
    else:
        from .forms import ProductForm
        form = ProductForm()

    return render(request, 'products/add_product.html', {'form': form})


@login_required(login_url='login')
def edit_product(request, pk):
    """Edit existing product."""
    from .models import ProductVariant
    
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        from .forms import ProductForm
        form = ProductForm(request.POST, request.FILES, instance=product)
        
        # Variant updates - form valid ho ya na ho, variants update karo
        for variant in product.variants.all():
            weight = request.POST.get(f'existing_variant_weight_{variant.id}')
            price = request.POST.get(f'existing_variant_price_{variant.id}')
            unit_type = request.POST.get(f'existing_variant_unit_type_{variant.id}', 'kg')
            stock = request.POST.get(f'existing_variant_stock_{variant.id}')
            
            if weight:
                variant.weight = weight
            if price:
                try:
                    variant.price = float(price)
                except ValueError:
                    pass
            variant.unit_type = unit_type
            if stock is not None and stock != '':
                try:
                    variant.stock = int(stock)
                except ValueError:
                    pass
            variant.save()
        
        # New variants add karo
        variant_index = 0
        while True:
            weight = request.POST.get(f'new_variant_weight_{variant_index}')
            if not weight:
                break
            price = request.POST.get(f'new_variant_price_{variant_index}')
            unit_type = request.POST.get(f'new_variant_unit_type_{variant_index}', 'kg')
            stock = request.POST.get(f'new_variant_stock_{variant_index}', '0')
            if weight and price:
                try:
                    stock_value = int(stock) if stock else 0
                except ValueError:
                    stock_value = 0
                from .models import ProductVariant as PV
                PV.objects.create(
                    product=product,
                    weight=weight,
                    price=float(price),
                    unit_type=unit_type,
                    stock=stock_value,
                    low_stock_alert=10,
                    is_active=True
                )
            variant_index += 1
        
        # Delete variants
        delete_variants = request.POST.getlist('delete_variants')
        if delete_variants:
            ProductVariant.objects.filter(id__in=delete_variants).delete()
        
        if form.is_valid():
            product = form.save(commit=False)
            # Default values for optional fields
            if not product.stock_quantity:
                product.stock_quantity = 0
            if not product.low_stock_threshold:
                product.low_stock_threshold = 10
            if not product.cost_price:
                product.cost_price = 0
            product.save()
            form.save_m2m()
            
            # Handle multiple images
            images = request.FILES.getlist('additional_images')
            for image in images:
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=False
                )
            
            # Handle image deletion
            delete_images = request.POST.getlist('delete_images')
            if delete_images:
                ProductImage.objects.filter(id__in=delete_images).delete()
            
            messages.success(request, '✓ Product updated successfully!')
            return redirect('product_list')
        else:
            pass  # Form will re-render with errors
    else:
        from .forms import ProductForm
        form = ProductForm(instance=product)

    # Get existing images
    existing_images = product.images.all()
    
    return render(request, 'products/edit_product.html', {
        'form': form, 
        'product': product,
        'existing_images': existing_images
    })



@login_required(login_url='login')
def delete_product(request, pk):
    """Delete product."""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.delete()
        messages.success(request, '✓ Product deleted successfully!')
        return redirect('product_list')

    return render(request, 'products/delete_product.html', {'product': product})


@login_required(login_url='login')
def low_stock_products(request):
    """Low stock and out of stock products page."""
    products = Product.objects.select_related('category').filter(
        stock_quantity__lte=F('low_stock_threshold')
    ).order_by('stock_quantity', '-id')

    search = request.GET.get('search', '').strip()

    if search:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=search) | Q(sku__icontains=search)
        )

    # Pagination
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'products/low_stock_products.html', context)




def _orders_for_period(period):
    """Return filtered Order queryset for the given period."""
    if period == 'All':
        return Order.objects.all()
    start_dt, end_dt = _get_period_date_range(period)
    qs = Order.objects.all()
    if start_dt is not None and end_dt is not None:
        qs = qs.filter(order_date__gte=start_dt, order_date__lte=end_dt)
    return qs


def _item_total_for_period(start_dt, end_dt, success_only=False):
    """Sum of (quantity * price) from OrderItem for orders in [start_dt, end_dt]. Optionally only Success orders.
    If start_dt/end_dt are None, calculates from all orders."""
    qs = OrderItem.objects.all()
    if start_dt is not None and end_dt is not None:
        qs = qs.filter(
        order__order_date__gte=start_dt,
        order__order_date__lte=end_dt,
    )
    if success_only:
        qs = qs.filter(order__payment_status='Success')
    return qs.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0


@login_required(login_url='login')
def dashboard(request):
    # Each section has its own period (like the original design) - default is "All"
    def get_period(key, default='All'):
        p = request.GET.get(key, default).strip()
        return p if p in PERIOD_CHOICES else default

    sales_period = get_period('sales_period', 'All')
    income_period = get_period('income_period', 'All')
    visitors_period = get_period('visitors_period', 'All')
    chart_period = get_period('chart_period', 'All')
    products_period = get_period('products_period', 'All')
    orders_period = get_period('orders_period', 'All')

    # Total Sales: from OrderItem (quantity * price) in period, so it's correct even if Order.total_amount is 0
    start_s, end_s = _get_period_date_range(sales_period)
    total_sales = _item_total_for_period(start_s, end_s, success_only=False)
    
    # Calculate sales percentage change
    prev_start_s, prev_end_s = _get_previous_period_range(sales_period)
    prev_sales = _item_total_for_period(prev_start_s, prev_end_s, success_only=False)
    sales_change = _calculate_percentage_change(total_sales, prev_sales)

    # Total Income: same but only Success orders
    start_i, end_i = _get_period_date_range(income_period)
    total_income = _item_total_for_period(start_i, end_i, success_only=True)
    
    # Calculate income percentage change
    prev_start_i, prev_end_i = _get_previous_period_range(income_period)
    prev_income = _item_total_for_period(prev_start_i, prev_end_i, success_only=True)
    income_change = _calculate_percentage_change(total_income, prev_income)

    # Visitors (its own period)
    orders_visitors = _orders_for_period(visitors_period)
    visitors = orders_visitors.values('customer').distinct().count()
    
    # Calculate visitors percentage change
    prev_visitors_period_start, prev_visitors_period_end = _get_previous_period_range(visitors_period)
    if prev_visitors_period_start and prev_visitors_period_end:
        prev_orders = Order.objects.filter(
            order_date__gte=prev_visitors_period_start,
            order_date__lte=prev_visitors_period_end
        )
        prev_visitors = prev_orders.values('customer').distinct().count()
    else:
        prev_visitors = 0
    visitors_change = _calculate_percentage_change(visitors, prev_visitors)

    # Chart: monthly SALES from OrderItem (quantity * price) for chart_period - saare orders, taaki line sale ke hisaab se dikhe
    from django.db.models.functions import TruncMonth
    start_c, end_c = _get_period_date_range(chart_period)
    chart_income = _item_total_for_period(start_c, end_c, success_only=True)
    if start_c is not None and end_c is not None:
        chart_monthly = (
            OrderItem.objects.filter(
                order__order_date__gte=start_c,
                order__order_date__lte=end_c,
            )
            .annotate(month=TruncMonth('order__order_date'))
            .values('month')
            .annotate(total=Sum(F('quantity') * F('price')))
            .order_by('month')
        )
    else:
        # If "All", show all orders grouped by month
        chart_monthly = (
            OrderItem.objects.annotate(month=TruncMonth('order__order_date'))
            .values('month')
            .annotate(total=Sum(F('quantity') * F('price')))
            .order_by('month')
        )
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    chart_labels = []
    chart_values = []
    for row in chart_monthly:
        chart_labels.append(month_names[row['month'].month - 1])
        chart_values.append(float(row['total']))
    if not chart_labels:
        chart_labels = month_names[:6]
        chart_values = [0] * 6

    # Top products (its own period) - with images
    start_p, end_p = _get_period_date_range(products_period)
    if start_p is not None and end_p is not None:
        top_products_qs = list(
            OrderItem.objects.filter(order__order_date__gte=start_p, order__order_date__lte=end_p)
            .values('product_name')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')[:3]
        )
    else:
        # If "All", show all products
        top_products_qs = list(
            OrderItem.objects.values('product_name')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')[:3]
        )
    
    # Fetch product images for top products
    top_products = []
    for item in top_products_qs:
        product_name = item['product_name']
        # Try to find matching product
        try:
            product = Product.objects.prefetch_related('images').get(name=product_name)
            product_image = None
            if product.image:
                product_image = product.image.url
            elif product.images.first():
                product_image = product.images.first().image.url
            
            top_products.append({
                'product_name': product_name,
                'total_qty': item['total_qty'],
                'product_image': product_image
            })
        except Product.DoesNotExist:
            # If product not found, show without image
            top_products.append({
                'product_name': product_name,
                'total_qty': item['total_qty'],
                'product_image': None
            })

    # Recent orders (its own period)
    recent_orders = _orders_for_period(orders_period).select_related('customer').order_by('-order_date')[:3]

    # Stock Alerts - Get actual low stock and out of stock products from Product model
    stock_alerts = []
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('low_stock_threshold')
    ).select_related('category').prefetch_related('images').order_by('stock_quantity')[:3]  # Top 3 low stock products for dashboard
    
    for product in low_stock_products:
        if product.stock_quantity == 0:
            status = 'out'
            status_text = 'Out of Stock'
        else:
            status = 'low'
            status_text = f'{product.stock_quantity} Units'
        
        # Get product image (main image or first additional image)
        product_image = None
        if product.image:
            product_image = product.image.url
        elif product.images.first():
            product_image = product.images.first().image.url
        
        stock_alerts.append({
            'product_name': product.name,
            'product_image': product_image,
            'status': status,
            'status_text': status_text,
            'units': product.stock_quantity
        })

    # Comments period filter
    comments_period = get_period('comments_period', 'All')

    context = {
        'period_choices': PERIOD_CHOICES,
        'sales_period': sales_period,
        'income_period': income_period,
        'visitors_period': visitors_period,
        'chart_period': chart_period,
        'products_period': products_period,
        'orders_period': orders_period,
        'comments_period': comments_period,
        'total_sales': total_sales,
        'sales_change': sales_change,
        'total_income': total_income,
        'income_change': income_change,
        'visitors': visitors,
        'visitors_change': visitors_change,
        'chart_income': chart_income,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_values_json': json.dumps(chart_values),
        'top_products': top_products,
        'recent_orders': recent_orders,
        'stock_alerts': stock_alerts,
    }
    return render(request, 'dashboard.html', context)

def category_list(request):
    category_list = Category.objects.all().order_by('id')
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    if search:
        # Match: (1) name contains search or search contains name
        # (2) OR fuzzy match for typos (e.g. "vegetables" matches "Vagetables")
        search_lower = search.lower()
        matching_ids = []
        for cat in category_list:
            name_lower = cat.name.lower().strip()
            if search_lower in name_lower or name_lower in search_lower:
                matching_ids.append(cat.id)
            elif SequenceMatcher(None, search_lower, name_lower).ratio() >= 0.8:
                matching_ids.append(cat.id)
        category_list = category_list.filter(id__in=matching_ids)

    if status_filter == 'active':
        category_list = category_list.filter(is_active=True)
    elif status_filter == 'inactive':
        category_list = category_list.filter(is_active=False)

    paginator = Paginator(category_list, 12)   # ✅ ek page me 12 category (card layout)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
    }
    return render(request, 'category/category_list.html', context)


# ADD CATEGORY
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                return redirect('category_list')
            except Exception as e:
                # Handle duplicate category error
                form.add_error('name', 'A category with this name already exists.')
    else:
        form = CategoryForm()

    return render(request, 'category/add_category.html', {
        'form': form
    })


def edit_category(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == "POST":
        form = CategoryForm(
            request.POST,
            request.FILES,
            instance=category
        )
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'category/edit_category.html', {
        'form': form,
        'category': category
    })

def delete_category(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == 'POST':
        category.delete()
        return redirect('category_list')

    return render(request, 'category/delete_category.html', {
        'category': category
    })


# ==========================================
# SUBCATEGORY MANAGEMENT
# ==========================================

def subcategory_list(request):
    subcategory_list = SubCategory.objects.select_related('category').all().order_by('id')
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    category_filter = request.GET.get('category', '').strip()
    
    if search:
        search_lower = search.lower()
        matching_ids = []
        for subcat in subcategory_list:
            name_lower = subcat.name.lower().strip()
            if search_lower in name_lower or name_lower in search_lower:
                matching_ids.append(subcat.id)
            elif SequenceMatcher(None, search_lower, name_lower).ratio() >= 0.8:
                matching_ids.append(subcat.id)
        subcategory_list = subcategory_list.filter(id__in=matching_ids)

    if status_filter == 'active':
        subcategory_list = subcategory_list.filter(is_active=True)
    elif status_filter == 'inactive':
        subcategory_list = subcategory_list.filter(is_active=False)
    
    if category_filter:
        subcategory_list = subcategory_list.filter(category_id=category_filter)

    paginator = Paginator(subcategory_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'categories': categories,
    }
    return render(request, 'subcategory/subcategory_list.html', context)


def add_subcategory(request):
    if request.method == "POST":
        form = SubCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                return redirect('subcategory_list')
            except Exception as e:
                # Handle duplicate subcategory error
                form.add_error('name', 'A subcategory with this name already exists in the selected category.')
    else:
        form = SubCategoryForm()

    return render(request, 'subcategory/add_subcategory.html', {
        'form': form
    })


def edit_subcategory(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)

    if request.method == "POST":
        form = SubCategoryForm(
            request.POST,
            request.FILES,
            instance=subcategory
        )
        if form.is_valid():
            form.save()
            return redirect('subcategory_list')
    else:
        form = SubCategoryForm(instance=subcategory)

    return render(request, 'subcategory/edit_subcategory.html', {
        'form': form,
        'subcategory': subcategory
    })


def delete_subcategory(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)

    if request.method == 'POST':
        subcategory.delete()
        return redirect('subcategory_list')

    return render(request, 'subcategory/delete_subcategory.html', {
        'subcategory': subcategory
    })


# ==========================================
# OFFER & DISCOUNT MANAGEMENT
# ==========================================

def offer_list(request):
    offer_list = Offer.objects.all().order_by('-created_at')
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()
    
    if search:
        search_lower = search.lower()
        matching_ids = []
        for offer in offer_list:
            name_lower = offer.name.lower().strip()
            if search_lower in name_lower or name_lower in search_lower:
                matching_ids.append(offer.id)
            elif SequenceMatcher(None, search_lower, name_lower).ratio() >= 0.8:
                matching_ids.append(offer.id)
        offer_list = offer_list.filter(id__in=matching_ids)

    if status_filter == 'active':
        offer_list = offer_list.filter(is_active=True)
    elif status_filter == 'inactive':
        offer_list = offer_list.filter(is_active=False)
    
    if type_filter:
        offer_list = offer_list.filter(discount_type=type_filter)

    paginator = Paginator(offer_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'type_filter': type_filter,
    }
    return render(request, 'offers/offer_list.html', context)


def add_offer(request):
    if request.method == "POST":
        form = OfferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('offer_list')
    else:
        form = OfferForm()

    return render(request, 'offers/add_offer.html', {
        'form': form
    })


def edit_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk)

    if request.method == "POST":
        form = OfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            return redirect('offer_list')
    else:
        form = OfferForm(instance=offer)

    return render(request, 'offers/edit_offer.html', {
        'form': form,
        'offer': offer
    })


def delete_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk)

    if request.method == 'POST':
        offer.delete()
        return redirect('offer_list')

    return render(request, 'offers/delete_offer.html', {
        'offer': offer
    })


# Order list period choices: All + same as dashboard
ORDER_PERIOD_CHOICES = ['All'] + PERIOD_CHOICES

# ORDER LIST + PAGINATION
def order_list(request):
    orders = Order.objects.select_related('customer').prefetch_related('items').order_by('-id')
    search = request.GET.get('search', '').strip()
    period = request.GET.get('period', 'All').strip()
    if period not in ORDER_PERIOD_CHOICES:
        period = 'All'

    # Filter by time period only when not "All"
    if period and period != 'All':
        start_dt, end_dt = _get_period_date_range(period)
        if start_dt is not None and end_dt is not None:
            orders = orders.filter(order_date__gte=start_dt, order_date__lte=end_dt)

    if search:
        # Match: order_id or customer name contains search, or fuzzy match (typos)
        search_lower = search.lower()
        matching_ids = []
        for order in orders:
            order_id_lower = (order.order_id or '').lower()
            customer_name_lower = (order.customer.name or '').lower().strip()
            if (search_lower in order_id_lower or order_id_lower in search_lower or
                    search_lower in customer_name_lower or customer_name_lower in search_lower):
                matching_ids.append(order.id)
            elif (SequenceMatcher(None, search_lower, order_id_lower).ratio() >= 0.8 or
                  SequenceMatcher(None, search_lower, customer_name_lower).ratio() >= 0.8):
                matching_ids.append(order.id)
        orders = orders.filter(id__in=matching_ids)

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate accurate totals for each order - use invoice total if exists, else items total
    orders_with_totals = []
    for order in page_obj:
        items = order.items.all()
        
        # Check if invoice exists for this order
        try:
            invoice = order.invoice
            # Use invoice total (includes GST, discount, etc.)
            grand_total = invoice.total_amount
        except:
            # No invoice, calculate simple total from OrderItems
            grand_total = items.aggregate(
                total=Sum(F('quantity') * F('price'))
            )['total'] or 0
        
        # Calculate total items (sum of quantities)
        total_items = items.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        # Add calculated values to order object
        order.calculated_total_amount = grand_total
        order.calculated_total_items = total_items
        orders_with_totals.append(order)

    total_orders = orders.count()
    success_count = orders.filter(payment_status="Success").count()
    pending_count = orders.filter(payment_status="Pending").count()
    cancelled_count = orders.filter(payment_status="Cancelled").count()

    # Calculate stats for all orders (not just filtered)
    all_orders = Order.objects.all()
    total_orders_count = all_orders.count()
    pending_orders_count = all_orders.filter(payment_status='Pending').count()
    success_orders_count = all_orders.filter(payment_status='Success').count()
    
    # Calculate average order value from success orders - use invoice total if exists
    success_orders = all_orders.filter(payment_status='Success')
    if success_orders_count > 0:
        total_success_amount = 0
        for order in success_orders:
            try:
                # Use invoice total if exists
                invoice = order.invoice
                order_total = invoice.total_amount
            except:
                # No invoice, calculate from items
                items = order.items.all()
                order_total = items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
            total_success_amount += order_total
        avg_order_value = total_success_amount / success_orders_count
    else:
        avg_order_value = 0

    context = {
        'orders': page_obj,
        'page_obj': page_obj,
        'total_orders': total_orders,
        'success_count': success_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'search': search,
        'period': period,
        'period_choices': ORDER_PERIOD_CHOICES,
        'total_orders_count': total_orders_count,
        'pending_orders_count': pending_orders_count,
        'success_orders_count': success_orders_count,
        'avg_order_value': avg_order_value,
    }

    return render(request, 'orders/order_list.html', context)


# ORDER DETAIL
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)

    items = order.items.all()

    # Calculate total items (sum of quantities) from OrderItems
    total_items = items.aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    # Check if invoice exists for this order
    try:
        invoice = order.invoice
        # Use invoice total (includes GST, discount, etc.)
        grand_total = invoice.total_amount
        has_invoice = True
        subtotal = invoice.subtotal
        discount = invoice.discount
        tax_amount = invoice.tax_amount
        tax_percentage = invoice.tax_percentage
    except:
        # No invoice, calculate simple total from OrderItems
        grand_total = items.aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0
        has_invoice = False
        subtotal = grand_total
        discount = 0
        tax_amount = 0
        tax_percentage = 0

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'items': items,
        'grand_total': grand_total,
        'total_items': total_items,
        'has_invoice': has_invoice,
        'subtotal': subtotal,
        'discount': discount,
        'tax_amount': tax_amount,
        'tax_percentage': tax_percentage,
    })


# EDIT ORDER
def edit_order(request, pk):
    order = Order.objects.get(pk=pk)
    customers = Customer.objects.all()

    # Calculate total items
    order.total_items = order.items.aggregate(
        total=Sum('quantity')
    )['total'] or 0

    # Check if invoice exists for this order
    try:
        invoice = order.invoice
        # Use invoice total (includes GST, discount, etc.)
        order.grand_total = invoice.total_amount
        has_invoice = True
        subtotal = invoice.subtotal
        discount = invoice.discount
        tax_amount = invoice.tax_amount
        tax_percentage = invoice.tax_percentage
    except:
        # No invoice, calculate simple total from OrderItems
        order.grand_total = order.items.aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0
        has_invoice = False
        subtotal = order.grand_total
        discount = 0
        tax_amount = 0
        tax_percentage = 0

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        order.customer = Customer.objects.get(id=customer_id)
        order.payment_status = request.POST.get('payment_status')
        order.payment_method = request.POST.get('payment_method')

        order.save()
        return redirect('order_list')

    return render(request, 'orders/edit_order.html', {
        'order': order,
        'customers': customers,
        'total_items': order.total_items,
        'grand_total': order.grand_total,
        'has_invoice': has_invoice,
        'subtotal': subtotal,
        'discount': discount,
        'tax_amount': tax_amount,
        'tax_percentage': tax_percentage,
    })


# DELETE ORDER
def delete_order(request, pk):
    order = get_object_or_404(Order, pk=pk)

    items = order.items.all()
    grand_total = items.aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0

    if request.method == 'POST':
        order.delete()
        return redirect('order_list')

    return render(request, 'orders/delete_order.html', {
        'order': order,
        'grand_total': grand_total,
        'total_items': items.aggregate(
            total=Sum('quantity')
        )['total'] or 0
    })


# --------------------
# DELIVERY MANAGEMENT (Amazon-style track order)
# --------------------
DELIVERY_STAGES = [
    ("Order_Placed", "Order Placed", "order"),
    ("Confirmed", "Confirmed", "package"),
    ("Shipped", "Shipped", "truck"),
    ("Out_for_Delivery", "Out for Delivery", "map-pin"),
    ("Delivered", "Delivered", "check-circle"),
]


def delivery_list(request):
    """List all orders with delivery status - like Amazon delivery management."""
    orders = Order.objects.select_related('customer').prefetch_related('items').order_by('-order_date')
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if search:
        from django.db.models import Q
        orders = orders.filter(
            Q(order_id__icontains=search) | Q(customer__name__icontains=search)
        )
    if status_filter and status_filter in dict(Order.DELIVERY_STATUS_CHOICES):
        orders = orders.filter(delivery_status=status_filter)

    # Calculate total amount and total items for all filtered orders - use invoice total if exists
    total_amount = 0
    total_items = 0
    for order in orders:
        items = order.items.all()
        
        # Check if invoice exists
        try:
            invoice = order.invoice
            order_total = invoice.total_amount
        except:
            order_total = items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
        
        order_items = items.aggregate(total=Sum('quantity'))['total'] or 0
        total_amount += order_total
        total_items += order_items

    paginator = Paginator(orders, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Calculate accurate totals for each order - use invoice total if exists
    for order in page_obj:
        items = order.items.all()
        
        # Check if invoice exists for this order
        try:
            invoice = order.invoice
            # Use invoice total (includes GST, discount, etc.)
            grand_total = invoice.total_amount
        except:
            # No invoice, calculate simple total from OrderItems
            grand_total = items.aggregate(
                total=Sum(F('quantity') * F('price'))
            )['total'] or 0
        
        # Calculate total items (sum of quantities)
        order_total_items = items.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        # Add calculated values to order object
        order.calculated_total_amount = grand_total
        order.calculated_total_items = order_total_items
    
    return render(request, 'delivery/delivery_list.html', {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'delivery_choices': Order.DELIVERY_STATUS_CHOICES,
        'total_amount': total_amount,
        'total_items': total_items,
    })


def track_order(request, pk):
    """Amazon-style track order page with timeline."""
    order = get_object_or_404(Order.objects.select_related('customer'), pk=pk)
    items = order.items.all()
    
    # Check if invoice exists for this order
    try:
        invoice = order.invoice
        # Use invoice total (includes GST, discount, etc.)
        grand_total = invoice.total_amount
        has_invoice = True
        subtotal = invoice.subtotal
        discount = invoice.discount
        tax_amount = invoice.tax_amount
        tax_percentage = invoice.tax_percentage
    except:
        # No invoice, calculate simple total from OrderItems
        grand_total = items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
        has_invoice = False
        subtotal = grand_total
        discount = 0
        tax_amount = 0
        tax_percentage = 0
    
    current_index = next((i for i, (k, _, _) in enumerate(DELIVERY_STAGES) if k == order.delivery_status), 0)
    return render(request, 'delivery/track_order.html', {
        'order': order,
        'items': items,
        'grand_total': grand_total,
        'has_invoice': has_invoice,
        'subtotal': subtotal,
        'discount': discount,
        'tax_amount': tax_amount,
        'tax_percentage': tax_percentage,
        'stages': DELIVERY_STAGES,
        'current_index': current_index,
        'delivery_choices': Order.DELIVERY_STATUS_CHOICES,
    })


def update_delivery_status(request, pk):
    """Update order delivery status (from track page)."""
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('delivery_status', '').strip()
        if new_status in dict(Order.DELIVERY_STATUS_CHOICES):
            order.delivery_status = new_status
            order.save()
    return redirect('track_order', pk=pk)


# --------------------
# REPORTS VIEWS
# --------------------
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.db.models import Max
from django.db.models.functions import TruncDate, TruncMonth

from .models import Product
from .models import Invoice, InvoiceItem, Tax
from .reports import (
    generate_table_report_pdf,
    generate_sales_report_pdf,
    generate_customer_report_pdf,
    generate_inventory_report_pdf,
    generate_daily_sales_report_pdf,
    generate_monthly_sales_report_pdf,
    generate_product_wise_sales_report_pdf,
    generate_low_stock_report_pdf,
    generate_customer_purchase_report_pdf,
    generate_profit_loss_report_pdf,
    generate_invoice_pdf,
)

COMPANY_NAME = "Grocery Admin"


def _fmt_money(v):
    return f"₹{float(v):,.2f}"


def _get_date_range_from_request(request):
    """Return (from_date, to_date, start_dt, end_dt) for report filtering."""
    today = timezone.localdate()
    default_from = today - timedelta(days=30)

    from_str = (request.GET.get('from_date') or '').strip()
    to_str = (request.GET.get('to_date') or '').strip()
    from_date = parse_date(from_str) or default_from
    to_date = parse_date(to_str) or today
    if from_date > to_date:
        from_date, to_date = to_date, from_date

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(from_date, datetime.min.time()), timezone=tz)
    end_dt = timezone.make_aware(datetime.combine(to_date, datetime.max.time()), timezone=tz)
    return from_date, to_date, start_dt, end_dt


# --------------------
# INVOICE + TAX VIEWS
# --------------------
@login_required(login_url='login')
def invoice_list(request):
    search = (request.GET.get('search') or '').strip()
    status = (request.GET.get('status') or '').strip()

    invoices = Invoice.objects.select_related('order', 'customer', 'tax').order_by('-issue_date')
    if status in dict(Invoice.PAYMENT_STATUS_CHOICES):
        invoices = invoices.filter(payment_status=status)
    if search:
        from django.db.models import Q
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(order__order_id__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(transaction_id__icontains=search)
        )

    # Summary
    total_invoices = invoices.count()
    paid_count = invoices.filter(payment_status="Paid").count()
    pending_count = invoices.filter(payment_status="Pending").count()
    cancelled_count = invoices.filter(payment_status="Cancelled").count()
    total_amount = invoices.aggregate(s=Sum('total_amount'))['s'] or 0

    paginator = Paginator(invoices, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'invoices/invoice_list.html', {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_invoices': total_invoices,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'total_amount': total_amount,
        'status_choices': Invoice.PAYMENT_STATUS_CHOICES,
    })


@login_required(login_url='login')
def generate_invoice(request, order_pk):
    """Create invoice from an order (idempotent)."""
    order = get_object_or_404(Order.objects.select_related('customer').prefetch_related('items'), pk=order_pk)
    if hasattr(order, 'invoice'):
        return redirect('invoice_detail', pk=order.invoice.pk)

    invoice = Invoice.objects.create(order=order, customer=order.customer)

    # Copy items snapshot
    items = order.items.all()
    for it in items:
        InvoiceItem.objects.create(
            invoice=invoice,
            product_name=it.product_name,
            quantity=it.quantity,
            unit_price=it.price,
        )

    invoice.recalculate(save=True)
    return redirect('invoice_detail', pk=invoice.pk)


@login_required(login_url='login')
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('order', 'customer', 'tax').prefetch_related('items'), pk=pk)

    if request.method == 'POST':
        from .forms import InvoiceUpdateForm
        form = InvoiceUpdateForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save()
            invoice.recalculate(save=True)
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        from .forms import InvoiceUpdateForm
        form = InvoiceUpdateForm(instance=invoice)

    return render(request, 'invoices/invoice_detail.html', {
        'invoice': invoice,
        'items': invoice.items.all(),
        'form': form,
    })


@login_required(login_url='login')
def download_invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('order', 'customer', 'tax').prefetch_related('items'), pk=pk)
    pdf_buffer = generate_invoice_pdf(company_name=COMPANY_NAME, invoice=invoice)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=\"{invoice.invoice_number}.pdf\"'
    return response


@login_required(login_url='login')
def tax_list(request):
    taxes = Tax.objects.all().order_by('-is_active', 'tax_name')
    return render(request, 'taxes/tax_list.html', {'taxes': taxes})


@login_required(login_url='login')
def add_tax(request):
    from .forms import TaxForm
    if request.method == 'POST':
        form = TaxForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tax_list')
    else:
        form = TaxForm()
    return render(request, 'taxes/tax_form.html', {'form': form, 'title': 'Add Tax'})


@login_required(login_url='login')
def edit_tax(request, pk):
    from .forms import TaxForm
    tax = get_object_or_404(Tax, pk=pk)
    if request.method == 'POST':
        form = TaxForm(request.POST, instance=tax)
        if form.is_valid():
            form.save()
            return redirect('tax_list')
    else:
        form = TaxForm(instance=tax)
    return render(request, 'taxes/tax_form.html', {'form': form, 'title': 'Edit Tax'})


@login_required(login_url='login')
def delete_tax(request, pk):
    tax = get_object_or_404(Tax, pk=pk)
    if request.method == 'POST':
        tax.delete()
        return redirect('tax_list')
    return render(request, 'taxes/tax_delete.html', {'tax': tax})

def reports_dashboard(request):
    """Main reports dashboard page"""
    return render(request, 'reports/reports_dashboard.html', {
        'period_choices': PERIOD_CHOICES,
    })


@login_required(login_url='login')
def daily_sales_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)

    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by date and calculate totals using invoice amounts
    from collections import defaultdict
    daily_data = defaultdict(lambda: {'orders': set(), 'items': 0, 'cost': 0, 'revenue': 0})
    
    for order in orders_qs:
        day = order.order_date.date()
        daily_data[day]['orders'].add(order.id)
        
        items = order.items.all()
        daily_data[day]['items'] += items.aggregate(s=Sum('quantity'))['s'] or 0
        daily_data[day]['cost'] += items.aggregate(s=Sum(F('quantity') * F('cost_price')))['s'] or 0
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            daily_data[day]['revenue'] += invoice.total_amount
        except:
            daily_data[day]['revenue'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0

    rows = []
    total_orders = 0
    total_items = 0
    total_cost = 0
    total_revenue = 0
    
    for day in sorted(daily_data.keys()):
        data = daily_data[day]
        orders_count = len(data['orders'])
        items_sold = data['items']
        cost = data['cost']
        revenue = data['revenue']
        profit = revenue - cost
        
        total_orders += orders_count
        total_items += items_sold
        total_cost += cost
        total_revenue += revenue
        
        rows.append([day.strftime('%Y-%m-%d'), orders_count, items_sold, _fmt_money(cost), _fmt_money(revenue), _fmt_money(profit)])

    total_profit = total_revenue - total_cost
    
    totals = [
        ("Total Orders", total_orders),
        ("Total Items Sold", total_items),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total Profit", _fmt_money(total_profit)),
    ]

    download_url = f"{reverse('download_daily_sales_report')}?from_date={from_date}&to_date={to_date}"
    return render(request, 'reports/view_report.html', {
        'report_title': "Daily Sales Report",
        'report_subtitle': "Daily order and revenue summary.",
        'from_date': from_date,
        'to_date': to_date,
        'columns': ["Date", "Orders", "Items Sold", "Cost", "Revenue", "Profit"],
        'rows': rows,
        'totals': totals,
        'download_url': download_url,
    })


@login_required(login_url='login')
def download_daily_sales_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    
    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by date and calculate totals using invoice amounts
    from collections import defaultdict
    daily_data = defaultdict(lambda: {'orders': set(), 'items': 0, 'cost': 0, 'revenue': 0})
    
    for order in orders_qs:
        day = order.order_date.date()
        daily_data[day]['orders'].add(order.id)
        
        items = order.items.all()
        daily_data[day]['items'] += items.aggregate(s=Sum('quantity'))['s'] or 0
        
        # Cost from items
        for item in items:
            if item.cost_price and item.cost_price > 0:
                daily_data[day]['cost'] += item.quantity * item.cost_price
            elif item.product:
                daily_data[day]['cost'] += item.quantity * (item.product.cost_price or 0)
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            daily_data[day]['revenue'] += invoice.total_amount
        except:
            daily_data[day]['revenue'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0

    rows = []
    total_orders = 0
    total_items = 0
    total_cost = 0
    total_revenue = 0
    
    for day in sorted(daily_data.keys()):
        data = daily_data[day]
        orders_count = len(data['orders'])
        items_sold = data['items']
        cost = data['cost']
        revenue = data['revenue']
        profit = revenue - cost
        
        total_orders += orders_count
        total_items += items_sold
        total_cost += cost
        total_revenue += revenue
        
        rows.append([day.strftime('%Y-%m-%d'), str(orders_count), str(items_sold), _fmt_money(cost), _fmt_money(revenue), _fmt_money(profit)])

    total_profit = total_revenue - total_cost
    
    totals = [
        ("Total Orders", str(total_orders)),
        ("Total Items Sold", str(total_items)),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total Profit", _fmt_money(total_profit)),
    ]

    pdf_buffer = generate_daily_sales_report_pdf(
        company_name=COMPANY_NAME,
        rows=rows,
        from_date=str(from_date),
        to_date=str(to_date),
        totals=totals,
    )
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="daily_sales_{from_date}_{to_date}.pdf"'
    return response


@login_required(login_url='login')
def monthly_sales_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    
    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by month and calculate totals using invoice amounts
    from collections import defaultdict
    monthly_data = defaultdict(lambda: {'orders': set(), 'items': 0, 'cost': 0, 'revenue': 0})
    
    for order in orders_qs:
        month = order.order_date.strftime('%Y-%m')
        monthly_data[month]['orders'].add(order.id)
        
        items = order.items.all()
        monthly_data[month]['items'] += items.aggregate(s=Sum('quantity'))['s'] or 0
        monthly_data[month]['cost'] += items.aggregate(s=Sum(F('quantity') * F('cost_price')))['s'] or 0
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            monthly_data[month]['revenue'] += invoice.total_amount
        except:
            monthly_data[month]['revenue'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0

    rows = []
    total_orders = 0
    total_items = 0
    total_cost = 0
    total_revenue = 0
    
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        orders_count = len(data['orders'])
        items_sold = data['items']
        cost = data['cost']
        revenue = data['revenue']
        profit = revenue - cost
        
        total_orders += orders_count
        total_items += items_sold
        total_cost += cost
        total_revenue += revenue
        
        rows.append([month, orders_count, items_sold, _fmt_money(cost), _fmt_money(revenue), _fmt_money(profit)])

    total_profit = total_revenue - total_cost
    
    totals = [
        ("Total Orders", total_orders),
        ("Total Items Sold", total_items),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total Profit", _fmt_money(total_profit)),
    ]

    download_url = f"{reverse('download_monthly_sales_report')}?from_date={from_date}&to_date={to_date}"
    return render(request, 'reports/view_report.html', {
        'report_title': "Monthly Sales Report",
        'report_subtitle': "Monthly order and revenue summary.",
        'from_date': from_date,
        'to_date': to_date,
        'columns': ["Month", "Orders", "Items Sold", "Cost", "Revenue", "Profit"],
        'rows': rows,
        'totals': totals,
        'download_url': download_url,
    })


@login_required(login_url='login')
def download_monthly_sales_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    
    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by month and calculate totals using invoice amounts
    from collections import defaultdict
    monthly_data = defaultdict(lambda: {'orders': set(), 'items': 0, 'cost': 0, 'revenue': 0})
    
    for order in orders_qs:
        month = order.order_date.strftime('%Y-%m')
        monthly_data[month]['orders'].add(order.id)
        
        items = order.items.all()
        monthly_data[month]['items'] += items.aggregate(s=Sum('quantity'))['s'] or 0
        
        # Cost from items
        for item in items:
            if item.cost_price and item.cost_price > 0:
                monthly_data[month]['cost'] += item.quantity * item.cost_price
            elif item.product:
                monthly_data[month]['cost'] += item.quantity * (item.product.cost_price or 0)
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            monthly_data[month]['revenue'] += invoice.total_amount
        except:
            monthly_data[month]['revenue'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0

    rows = []
    total_orders = 0
    total_items = 0
    total_cost = 0
    total_revenue = 0
    
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        orders_count = len(data['orders'])
        items_sold = data['items']
        cost = data['cost']
        revenue = data['revenue']
        profit = revenue - cost
        
        total_orders += orders_count
        total_items += items_sold
        total_cost += cost
        total_revenue += revenue
        
        # Format month as "Jan 2026"
        from datetime import datetime
        month_obj = datetime.strptime(month, '%Y-%m')
        month_str = month_obj.strftime('%b %Y')
        
        rows.append([month_str, str(orders_count), str(items_sold), _fmt_money(cost), _fmt_money(revenue), _fmt_money(profit)])

    total_profit = total_revenue - total_cost
    
    totals = [
        ("Total Orders", str(total_orders)),
        ("Total Items Sold", str(total_items)),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total Profit", _fmt_money(total_profit)),
    ]

    pdf_buffer = generate_monthly_sales_report_pdf(
        company_name=COMPANY_NAME,
        rows=rows,
        from_date=str(from_date),
        to_date=str(to_date),
        totals=totals,
    )
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="monthly_sales_{from_date}_{to_date}.pdf"'
    return response


@login_required(login_url='login')
def product_wise_sales_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    items_qs = OrderItem.objects.filter(order__order_date__gte=start_dt, order__order_date__lte=end_dt)
    products = (
        items_qs.values('product_name')
        .annotate(
            qty_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('price')),
            cogs=Sum(F('quantity') * F('cost_price')),
        )
        .order_by('-revenue')
    )
    rows = []
    total_qty = 0
    total_revenue = 0
    total_cogs = 0
    for r in products:
        name = r['product_name']
        qty = r['qty_sold'] or 0
        revenue = r['revenue'] or 0
        cogs = r['cogs'] or 0
        profit = revenue - cogs
        total_qty += qty
        total_revenue += revenue
        total_cogs += cogs
        rows.append([name, qty, _fmt_money(revenue), _fmt_money(cogs), _fmt_money(profit)])

    totals = [
        ("Total Qty Sold", total_qty),
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total COGS", _fmt_money(total_cogs)),
        ("Total Profit", _fmt_money(total_revenue - total_cogs)),
    ]
    download_url = f"{reverse('download_product_wise_sales_report')}?from_date={from_date}&to_date={to_date}"
    return render(request, 'reports/view_report.html', {
        'report_title': "Product Wise Sales Report",
        'report_subtitle': "Sales summary by product (includes profit if cost price is set).",
        'from_date': from_date,
        'to_date': to_date,
        'columns': ["Product", "Qty Sold", "Revenue", "COGS", "Profit"],
        'rows': rows,
        'totals': totals,
        'download_url': download_url,
    })


@login_required(login_url='login')
def download_product_wise_sales_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    items_qs = OrderItem.objects.filter(order__order_date__gte=start_dt, order__order_date__lte=end_dt)
    products = (
        items_qs.values('product_name')
        .annotate(
            qty_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('price')),
            cogs=Sum(F('quantity') * F('cost_price')),
        )
        .order_by('-revenue')
    )
    rows = []
    total_qty = 0
    total_revenue = 0
    total_cogs = 0
    for r in products:
        name = r['product_name']
        qty = r['qty_sold'] or 0
        revenue = r['revenue'] or 0
        cogs = r['cogs'] or 0
        profit = revenue - cogs
        total_qty += qty
        total_revenue += revenue
        total_cogs += cogs
        rows.append([name, str(qty), _fmt_money(revenue), _fmt_money(cogs), _fmt_money(profit)])
    totals = [
        ("Total Qty Sold", str(total_qty)),
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total COGS", _fmt_money(total_cogs)),
        ("Total Profit", _fmt_money(total_revenue - total_cogs)),
    ]

    pdf_buffer = generate_product_wise_sales_report_pdf(
        company_name=COMPANY_NAME,
        rows=rows,
        from_date=str(from_date),
        to_date=str(to_date),
        totals=totals,
    )
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="product_sales_{from_date}_{to_date}.pdf"'
    return response


@login_required(login_url='login')
def low_stock_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    products = Product.objects.select_related('category').filter(updated_at__gte=start_dt, updated_at__lte=end_dt).order_by('stock_quantity')
    low_products = []
    for p in products:
        threshold = p.low_stock_threshold or 0
        if p.stock_quantity <= threshold:
            low_products.append(p)

    rows = []
    for p in low_products:
        rows.append([
            p.name,
            p.sku or "-",
            p.category.name if p.category else "-",
            p.stock_quantity,
            p.low_stock_threshold,
            "Low Stock" if p.stock_quantity > 0 else "Out of Stock",
        ])

    totals = [("Low stock products", len(low_products))]
    download_url = f"{reverse('download_low_stock_report')}?from_date={from_date}&to_date={to_date}"
    return render(request, 'reports/view_report.html', {
        'report_title': "Low Stock Report",
        'report_subtitle': "Products where stock is below (or equal to) the product threshold.",
        'from_date': from_date,
        'to_date': to_date,
        'columns': ["Product", "SKU", "Category", "Stock", "Threshold", "Status"],
        'rows': rows,
        'totals': totals,
        'download_url': download_url,
    })


@login_required(login_url='login')
def download_low_stock_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    products = Product.objects.select_related('category').filter(updated_at__gte=start_dt, updated_at__lte=end_dt).order_by('stock_quantity')
    rows = []
    low_count = 0
    for p in products:
        threshold = p.low_stock_threshold or 0
        if p.stock_quantity <= threshold:
            low_count += 1
            rows.append([
                p.name,
                p.sku or "-",
                p.category.name if p.category else "-",
                str(p.stock_quantity),
                str(p.low_stock_threshold),
                "Low Stock" if p.stock_quantity > 0 else "Out of Stock",
            ])
    totals = [("Low stock products", str(low_count))]
    pdf_buffer = generate_low_stock_report_pdf(
        company_name=COMPANY_NAME,
        rows=rows,
        from_date=str(from_date),
        to_date=str(to_date),
        totals=totals,
    )
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="low_stock_{from_date}_{to_date}.pdf"'
    return response


@login_required(login_url='login')
def customer_purchase_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    
    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by customer and calculate totals using invoice amounts
    from collections import defaultdict
    customer_data = defaultdict(lambda: {'orders': set(), 'items': 0, 'cost': 0, 'spent': 0, 'last_purchase': None, 'email': ''})
    
    for order in orders_qs:
        customer_name = order.customer.name
        customer_data[customer_name]['email'] = order.customer.email or ''
        customer_data[customer_name]['orders'].add(order.id)
        
        items = order.items.all()
        customer_data[customer_name]['items'] += items.aggregate(s=Sum('quantity'))['s'] or 0
        customer_data[customer_name]['cost'] += items.aggregate(s=Sum(F('quantity') * F('cost_price')))['s'] or 0
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            customer_data[customer_name]['spent'] += invoice.total_amount
        except:
            customer_data[customer_name]['spent'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0
        
        # Track last purchase date
        if customer_data[customer_name]['last_purchase'] is None or order.order_date > customer_data[customer_name]['last_purchase']:
            customer_data[customer_name]['last_purchase'] = order.order_date

    rows = []
    total_orders = 0
    total_items = 0
    total_cost = 0
    total_spent = 0
    
    # Sort by spent (descending)
    for customer_name in sorted(customer_data.keys(), key=lambda x: customer_data[x]['spent'], reverse=True):
        data = customer_data[customer_name]
        orders_count = len(data['orders'])
        items_count = data['items']
        cost = data['cost']
        spent = data['spent']
        profit = spent - cost
        
        total_orders += orders_count
        total_items += items_count
        total_cost += cost
        total_spent += spent
        
        rows.append([
            customer_name,
            data['email'],
            orders_count,
            items_count,
            _fmt_money(cost),
            _fmt_money(spent),
            _fmt_money(profit),
            (data['last_purchase'].strftime('%Y-%m-%d') if data['last_purchase'] else "-"),
        ])

    total_profit = total_spent - total_cost
    
    totals = [
        ("Total Orders", total_orders),
        ("Total Items", total_items),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Spent", _fmt_money(total_spent)),
        ("Total Profit", _fmt_money(total_profit)),
    ]
    download_url = f"{reverse('download_customer_purchase_report')}?from_date={from_date}&to_date={to_date}"
    return render(request, 'reports/view_report.html', {
        'report_title': "Customer Purchase Report",
        'report_subtitle': "Customer-wise order count and spending within the date range.",
        'from_date': from_date,
        'to_date': to_date,
        'columns': ["Customer", "Email", "Orders", "Items", "Cost", "Revenue", "Profit", "Last Purchase"],
        'rows': rows,
        'totals': totals,
        'download_url': download_url,
    })


@login_required(login_url='login')
def download_customer_purchase_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    
    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by customer and calculate totals using invoice amounts
    from collections import defaultdict
    customer_data = defaultdict(lambda: {'orders': set(), 'items': 0, 'cost': 0, 'spent': 0, 'last_purchase': None, 'email': ''})
    
    for order in orders_qs:
        customer_name = order.customer.name
        customer_data[customer_name]['email'] = order.customer.email or ''
        customer_data[customer_name]['orders'].add(order.id)
        
        items = order.items.all()
        customer_data[customer_name]['items'] += items.aggregate(s=Sum('quantity'))['s'] or 0
        
        # Cost from items
        for item in items:
            if item.cost_price and item.cost_price > 0:
                customer_data[customer_name]['cost'] += item.quantity * item.cost_price
            elif item.product:
                customer_data[customer_name]['cost'] += item.quantity * (item.product.cost_price or 0)
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            customer_data[customer_name]['spent'] += invoice.total_amount
        except:
            customer_data[customer_name]['spent'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0
        
        # Track last purchase date
        if customer_data[customer_name]['last_purchase'] is None or order.order_date > customer_data[customer_name]['last_purchase']:
            customer_data[customer_name]['last_purchase'] = order.order_date

    rows = []
    total_orders = 0
    total_items = 0
    total_cost = 0
    total_spent = 0
    
    # Sort by spent (descending)
    for customer_name in sorted(customer_data.keys(), key=lambda x: customer_data[x]['spent'], reverse=True):
        data = customer_data[customer_name]
        orders_count = len(data['orders'])
        items_count = data['items']
        cost = data['cost']
        spent = data['spent']
        profit = spent - cost
        
        total_orders += orders_count
        total_items += items_count
        total_cost += cost
        total_spent += spent
        
        rows.append([
            customer_name,
            data['email'],
            str(orders_count),
            str(items_count),
            _fmt_money(cost),
            _fmt_money(spent),
            _fmt_money(profit),
            (data['last_purchase'].strftime('%Y-%m-%d') if data['last_purchase'] else "-"),
        ])

    total_profit = total_spent - total_cost
    
    totals = [
        ("Total Orders", str(total_orders)),
        ("Total Items", str(total_items)),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Spent", _fmt_money(total_spent)),
        ("Total Profit", _fmt_money(total_profit)),
    ]
    pdf_buffer = generate_customer_purchase_report_pdf(
        company_name=COMPANY_NAME,
        rows=rows,
        from_date=str(from_date),
        to_date=str(to_date),
        totals=totals,
    )
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="customer_purchase_{from_date}_{to_date}.pdf"'
    return response


@login_required(login_url='login')
def profit_loss_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    
    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by date and calculate revenue (from invoice) and COGS (from items)
    from collections import defaultdict
    daily_data = defaultdict(lambda: {'revenue': 0, 'cogs': 0})
    
    for order in orders_qs:
        day = order.order_date.date()
        
        items = order.items.all()
        # COGS always from items
        daily_data[day]['cogs'] += items.aggregate(s=Sum(F('quantity') * F('cost_price')))['s'] or 0
        
        # Revenue from invoice if exists
        try:
            invoice = order.invoice
            daily_data[day]['revenue'] += invoice.total_amount
        except:
            daily_data[day]['revenue'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0

    rows = []
    total_revenue = 0
    total_cogs = 0
    
    for day in sorted(daily_data.keys()):
        data = daily_data[day]
        revenue = data['revenue']
        cogs = data['cogs']
        profit = revenue - cogs
        
        total_revenue += revenue
        total_cogs += cogs
        
        rows.append([day.strftime('%Y-%m-%d'), _fmt_money(revenue), _fmt_money(cogs), _fmt_money(profit)])

    totals = [
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total COGS", _fmt_money(total_cogs)),
        ("Gross Profit", _fmt_money(total_revenue - total_cogs)),
    ]
    download_url = f"{reverse('download_profit_loss_report')}?from_date={from_date}&to_date={to_date}"
    return render(request, 'reports/view_report.html', {
        'report_title': "Profit & Loss Report",
        'report_subtitle': "Daily revenue vs cost (COGS). Set `cost_price` on products/items for accurate profit.",
        'from_date': from_date,
        'to_date': to_date,
        'columns': ["Date", "Revenue", "COGS", "Gross Profit"],
        'rows': rows,
        'totals': totals,
        'download_url': download_url,
    })


@login_required(login_url='login')
def download_profit_loss_report(request):
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)
    
    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by date and calculate revenue (from invoice) and COGS (from items)
    from collections import defaultdict
    daily_data = defaultdict(lambda: {'revenue': 0, 'cogs': 0})
    
    for order in orders_qs:
        day = order.order_date.date()
        
        items = order.items.all()
        
        # COGS from items
        for item in items:
            if item.cost_price and item.cost_price > 0:
                daily_data[day]['cogs'] += item.quantity * item.cost_price
            elif item.product:
                daily_data[day]['cogs'] += item.quantity * (item.product.cost_price or 0)
        
        # Revenue from invoice if exists
        try:
            invoice = order.invoice
            daily_data[day]['revenue'] += invoice.total_amount
        except:
            daily_data[day]['revenue'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0

    rows = []
    total_revenue = 0
    total_cogs = 0
    
    for day in sorted(daily_data.keys()):
        data = daily_data[day]
        revenue = data['revenue']
        cogs = data['cogs']
        profit = revenue - cogs
        
        total_revenue += revenue
        total_cogs += cogs
        
        rows.append([day.strftime('%Y-%m-%d'), _fmt_money(revenue), _fmt_money(cogs), _fmt_money(profit)])
    
    totals = [
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total COGS", _fmt_money(total_cogs)),
        ("Gross Profit", _fmt_money(total_revenue - total_cogs)),
    ]
    pdf_buffer = generate_profit_loss_report_pdf(
        company_name=COMPANY_NAME,
        rows=rows,
        from_date=str(from_date),
        to_date=str(to_date),
        totals=totals,
    )
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="profit_loss_{from_date}_{to_date}.pdf"'
    return response


@login_required(login_url='login')
def sales_report(request):
    """Sales report (same UI as other reports): date range + table + PDF."""
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)

    orders_qs = (
        Order.objects.select_related('customer')
        .prefetch_related('items')
        .filter(order_date__gte=start_dt, order_date__lte=end_dt)
        .order_by('-order_date')
    )

    # Calculate totals using invoice amounts where available
    total_orders = orders_qs.count()
    total_items = 0
    total_revenue = 0
    total_cost = 0
    
    for order in orders_qs:
        items = order.items.all()
        total_items += items.aggregate(s=Sum('quantity'))['s'] or 0
        
        # Cost from items - if cost_price is 0, try to get from product
        for item in items:
            if item.cost_price and item.cost_price > 0:
                total_cost += item.quantity * item.cost_price
            elif item.product:
                total_cost += item.quantity * (item.product.cost_price or 0)
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            total_revenue += invoice.total_amount
        except:
            total_revenue += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0

    rows = []
    for order in orders_qs[:200]:
        items = list(order.items.all())
        order_items = sum((i.quantity for i in items), 0)
        
        # Calculate cost - if cost_price is 0, try to get from product
        order_cost = 0
        for item in items:
            if item.cost_price and item.cost_price > 0:
                order_cost += item.quantity * item.cost_price
            elif item.product:
                order_cost += item.quantity * (item.product.cost_price or 0)
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            order_total = invoice.total_amount
        except:
            order_total = sum(((i.quantity * i.price) for i in items), 0)
        
        order_profit = order_total - order_cost
        
        rows.append([
            order.order_id,
            order.customer.name,
            order.order_date.strftime('%Y-%m-%d'),
            order_items,
            _fmt_money(order_cost),
            _fmt_money(order_total),
            _fmt_money(order_profit),
            order.payment_status,
        ])

    total_profit = total_revenue - total_cost
    
    totals = [
        ("Total Orders", total_orders),
        ("Total Items", total_items),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total Profit", _fmt_money(total_profit)),
    ]

    download_url = f"{reverse('download_sales_report')}?from_date={from_date}&to_date={to_date}"
    return render(request, 'reports/view_report.html', {
        'report_title': "Sales Report",
        'report_subtitle': "Order-wise sales within the selected date range.",
        'from_date': from_date,
        'to_date': to_date,
        'columns': ["Order ID", "Customer", "Date", "Items", "Cost", "Revenue", "Profit", "Status"],
        'rows': rows,
        'totals': totals,
        'download_url': download_url,
    })


@login_required(login_url='login')
def download_sales_report(request):
    """Download sales report (date range) as PDF."""
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)

    orders_qs = (
        Order.objects.select_related('customer')
        .prefetch_related('items')
        .filter(order_date__gte=start_dt, order_date__lte=end_dt)
        .order_by('-order_date')
    )
    
    total_orders = orders_qs.count()
    total_items = 0
    total_cost = 0
    total_revenue = 0
    
    # Calculate totals using invoice amounts
    for order in orders_qs:
        items = order.items.all()
        total_items += items.aggregate(s=Sum('quantity'))['s'] or 0
        
        # Cost from items
        for item in items:
            if item.cost_price and item.cost_price > 0:
                total_cost += item.quantity * item.cost_price
            elif item.product:
                total_cost += item.quantity * (item.product.cost_price or 0)
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            total_revenue += invoice.total_amount
        except:
            total_revenue += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0

    rows = []
    for order in orders_qs[:500]:
        items = list(order.items.all())
        order_items = sum((i.quantity for i in items), 0)
        
        # Calculate cost
        order_cost = 0
        for item in items:
            if item.cost_price and item.cost_price > 0:
                order_cost += item.quantity * item.cost_price
            elif item.product:
                order_cost += item.quantity * (item.product.cost_price or 0)
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            order_total = invoice.total_amount
        except:
            order_total = sum(((i.quantity * i.price) for i in items), 0)
        
        order_profit = order_total - order_cost
        
        rows.append([
            order.order_id,
            order.customer.name,
            order.order_date.strftime('%Y-%m-%d'),
            str(order_items),
            _fmt_money(order_cost),
            _fmt_money(order_total),
            _fmt_money(order_profit),
            order.payment_status,
        ])

    total_profit = total_revenue - total_cost
    
    totals = [
        ("Total Orders", str(total_orders)),
        ("Total Items", str(total_items)),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Revenue", _fmt_money(total_revenue)),
        ("Total Profit", _fmt_money(total_profit)),
    ]

    pdf_buffer = generate_table_report_pdf(
        company_name=COMPANY_NAME,
        report_title="Sales Report",
        date_range_text=f"Date range: {from_date} to {to_date}",
        columns=["Order ID", "Customer", "Date", "Items", "Cost", "Revenue", "Profit", "Status"],
        rows=rows,
        totals=totals,
    )

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=\"sales_report_{from_date}_{to_date}.pdf\"'
    return response


@login_required(login_url='login')
def customer_report(request):
    """Customer report (same UI as other reports): date range + table + PDF."""
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)

    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by customer and calculate totals using invoice amounts
    from collections import defaultdict
    customer_data = defaultdict(lambda: {'orders': set(), 'items': 0, 'cost': 0, 'spent': 0, 'last_purchase': None, 'email': '', 'gender': ''})
    
    for order in orders_qs:
        customer_name = order.customer.name
        customer_data[customer_name]['email'] = order.customer.email or ''
        customer_data[customer_name]['gender'] = order.customer.gender or '-'
        customer_data[customer_name]['orders'].add(order.id)
        
        items = order.items.all()
        customer_data[customer_name]['items'] += items.aggregate(s=Sum('quantity'))['s'] or 0
        customer_data[customer_name]['cost'] += items.aggregate(s=Sum(F('quantity') * F('cost_price')))['s'] or 0
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            customer_data[customer_name]['spent'] += invoice.total_amount
        except:
            customer_data[customer_name]['spent'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0
        
        # Track last purchase date
        if customer_data[customer_name]['last_purchase'] is None or order.order_date > customer_data[customer_name]['last_purchase']:
            customer_data[customer_name]['last_purchase'] = order.order_date

    rows = []
    total_orders = 0
    total_items = 0
    total_cost = 0
    total_spent = 0
    customer_count = 0
    
    # Sort by spent (descending)
    for customer_name in sorted(customer_data.keys(), key=lambda x: customer_data[x]['spent'], reverse=True):
        data = customer_data[customer_name]
        customer_count += 1
        orders_count = len(data['orders'])
        items_count = data['items']
        cost = data['cost']
        spent = data['spent']
        profit = spent - cost
        
        total_orders += orders_count
        total_items += items_count
        total_cost += cost
        total_spent += spent
        
        rows.append([
            customer_name,
            data['email'],
            data['gender'],
            orders_count,
            items_count,
            _fmt_money(cost),
            _fmt_money(spent),
            _fmt_money(profit),
            data['last_purchase'].strftime('%Y-%m-%d') if data['last_purchase'] else "-",
        ])

    total_profit = total_spent - total_cost
    
    totals = [
        ("Total Customers", customer_count),
        ("Total Orders", total_orders),
        ("Total Items", total_items),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Spent", _fmt_money(total_spent)),
        ("Total Profit", _fmt_money(total_profit)),
    ]

    download_url = f"{reverse('download_customer_report')}?from_date={from_date}&to_date={to_date}"
    return render(request, 'reports/view_report.html', {
        'report_title': "Customer Report",
        'report_subtitle': "Customer-wise purchases and totals within the selected date range.",
        'from_date': from_date,
        'to_date': to_date,
        'columns': ["Customer", "Email", "Gender", "Orders", "Items", "Cost", "Revenue", "Profit", "Last Purchase"],
        'rows': rows,
        'totals': totals,
        'download_url': download_url,
    })


@login_required(login_url='login')
def download_customer_report(request):
    """Download customer report (date range) as PDF."""
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)

    # Get all orders in date range
    orders_qs = Order.objects.filter(order_date__gte=start_dt, order_date__lte=end_dt).select_related('customer').prefetch_related('items')
    
    # Group by customer and calculate totals using invoice amounts
    from collections import defaultdict
    customer_data = defaultdict(lambda: {'orders': set(), 'items': 0, 'cost': 0, 'spent': 0, 'last_purchase': None, 'email': '', 'gender': ''})
    
    for order in orders_qs:
        customer_name = order.customer.name
        customer_data[customer_name]['email'] = order.customer.email or ''
        customer_data[customer_name]['gender'] = order.customer.gender or '-'
        customer_data[customer_name]['orders'].add(order.id)
        
        items = order.items.all()
        customer_data[customer_name]['items'] += items.aggregate(s=Sum('quantity'))['s'] or 0
        
        # Cost from items
        for item in items:
            if item.cost_price and item.cost_price > 0:
                customer_data[customer_name]['cost'] += item.quantity * item.cost_price
            elif item.product:
                customer_data[customer_name]['cost'] += item.quantity * (item.product.cost_price or 0)
        
        # Use invoice total if exists
        try:
            invoice = order.invoice
            customer_data[customer_name]['spent'] += invoice.total_amount
        except:
            customer_data[customer_name]['spent'] += items.aggregate(s=Sum(F('quantity') * F('price')))['s'] or 0
        
        # Track last purchase date
        if customer_data[customer_name]['last_purchase'] is None or order.order_date > customer_data[customer_name]['last_purchase']:
            customer_data[customer_name]['last_purchase'] = order.order_date

    rows = []
    total_orders = 0
    total_items = 0
    total_cost = 0
    total_spent = 0
    customer_count = 0
    
    # Sort by spent (descending)
    for customer_name in sorted(customer_data.keys(), key=lambda x: customer_data[x]['spent'], reverse=True):
        data = customer_data[customer_name]
        customer_count += 1
        orders_count = len(data['orders'])
        items_count = data['items']
        cost = data['cost']
        spent = data['spent']
        profit = spent - cost
        
        total_orders += orders_count
        total_items += items_count
        total_cost += cost
        total_spent += spent
        
        rows.append([
            customer_name,
            data['email'],
            data['gender'],
            str(orders_count),
            str(items_count),
            _fmt_money(cost),
            _fmt_money(spent),
            _fmt_money(profit),
            data['last_purchase'].strftime('%Y-%m-%d') if data['last_purchase'] else "-",
        ])

    total_profit = total_spent - total_cost
    
    totals = [
        ("Total Customers", str(customer_count)),
        ("Total Orders", str(total_orders)),
        ("Total Items", str(total_items)),
        ("Total Cost", _fmt_money(total_cost)),
        ("Total Spent", _fmt_money(total_spent)),
        ("Total Profit", _fmt_money(total_profit)),
    ]

    pdf_buffer = generate_table_report_pdf(
        company_name=COMPANY_NAME,
        report_title="Customer Report",
        date_range_text=f"Date range: {from_date} to {to_date}",
        columns=["Customer", "Email", "Gender", "Orders", "Items", "Cost", "Revenue", "Profit", "Last Purchase"],
        rows=rows,
        totals=totals,
    )

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=\"customer_report_{from_date}_{to_date}.pdf\"'
    return response


@login_required(login_url='login')
def inventory_report(request):
    """Inventory report (same UI as other reports): date range + table + PDF."""
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)

    products_qs = (
        Product.objects.select_related('category')
        .filter(updated_at__gte=start_dt, updated_at__lte=end_dt)
        .filter(category__is_active=True)  # Only active categories
        .order_by('stock_quantity', 'name')
    )

    rows = []
    low_count = 0
    out_count = 0
    for p in products_qs[:500]:
        threshold = p.low_stock_threshold or 0
        if p.stock_quantity <= threshold:
            low_count += 1
        if p.stock_quantity == 0:
            out_count += 1
        rows.append([
            p.name,
            p.sku or "-",
            p.category.name if p.category else "-",
            p.stock_quantity,
            p.low_stock_threshold,
            "Active" if p.is_active else "Inactive",
        ])

    totals = [
        ("Total Products", products_qs.count()),
        ("Low Stock", low_count),
        ("Out of Stock", out_count),
    ]

    download_url = f"{reverse('download_inventory_report')}?from_date={from_date}&to_date={to_date}"
    return render(request, 'reports/view_report.html', {
        'report_title': "Inventory Report",
        'report_subtitle': "Product inventory and stock levels (filtered by product update date).",
        'from_date': from_date,
        'to_date': to_date,
        'columns': ["Product", "SKU", "Category", "Stock", "Threshold", "Status"],
        'rows': rows,
        'totals': totals,
        'download_url': download_url,
    })


@login_required(login_url='login')
def download_inventory_report(request):
    """Download inventory report (date range) as PDF."""
    from_date, to_date, start_dt, end_dt = _get_date_range_from_request(request)

    products_qs = (
        Product.objects.select_related('category')
        .filter(updated_at__gte=start_dt, updated_at__lte=end_dt)
        .filter(category__is_active=True)  # Only active categories
        .order_by('stock_quantity', 'name')
    )

    rows = []
    low_count = 0
    out_count = 0
    for p in products_qs:
        threshold = p.low_stock_threshold or 0
        if p.stock_quantity <= threshold:
            low_count += 1
        if p.stock_quantity == 0:
            out_count += 1
        rows.append([
            p.name,
            p.sku or "-",
            p.category.name if p.category else "-",
            str(p.stock_quantity),
            str(p.low_stock_threshold),
            "Active" if p.is_active else "Inactive",
        ])

    totals = [
        ("Total Products", str(products_qs.count())),
        ("Low Stock", str(low_count)),
        ("Out of Stock", str(out_count)),
    ]

    pdf_buffer = generate_table_report_pdf(
        company_name=COMPANY_NAME,
        report_title="Inventory Report",
        date_range_text=f"Date range: {from_date} to {to_date}",
        columns=["Product", "SKU", "Category", "Stock", "Threshold", "Status"],
        rows=rows,
        totals=totals,
    )

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=\"inventory_report_{from_date}_{to_date}.pdf\"'
    return response


# --------------------
# PAYMENT MANAGEMENT VIEWS
# --------------------
import json as json_module

def payment_dashboard(request):
    """Amazon-style payment management dashboard"""
    period = request.GET.get('period', 'All').strip()
    if period not in PERIOD_CHOICES:
        period = 'All'
    
    status = request.GET.get('status', '').strip()
    method = request.GET.get('method', '').strip()
    search = request.GET.get('search', '').strip()
    
    # Filter orders by period
    orders = Order.objects.select_related('customer').prefetch_related('items').order_by('-order_date')
    
    if period != 'All':
        start_dt, end_dt = _get_period_date_range(period)
        if start_dt and end_dt:
            orders = orders.filter(order_date__gte=start_dt, order_date__lte=end_dt)
    
    # Apply filters
    if status:
        orders = orders.filter(payment_status=status)
    
    if method:
        orders = orders.filter(payment_method=method)
    
    if search:
        from django.db.models import Q
        orders = orders.filter(
            Q(order_id__icontains=search) |
            Q(transaction_id__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(customer__email__icontains=search)
        )
    
    # Calculate statistics - use invoice totals where available
    total_revenue = 0
    for order in orders:
        try:
            invoice = order.invoice
            total_revenue += invoice.total_amount
        except:
            items = order.items.all()
            total_revenue += items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    success_orders = orders.filter(payment_status='Success')
    success_count = success_orders.count()
    success_amount = 0
    for order in success_orders:
        try:
            invoice = order.invoice
            success_amount += invoice.total_amount
        except:
            items = order.items.all()
            success_amount += items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    pending_orders = orders.filter(payment_status='Pending')
    pending_count = pending_orders.count()
    pending_amount = 0
    for order in pending_orders:
        try:
            invoice = order.invoice
            pending_amount += invoice.total_amount
        except:
            items = order.items.all()
            pending_amount += items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0

    failed_orders = orders.filter(payment_status='Cancelled')
    failed_count = failed_orders.count()
    failed_amount = 0
    for order in failed_orders:
        try:
            invoice = order.invoice
            failed_amount += invoice.total_amount
        except:
            items = order.items.all()
            failed_amount += items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    total_transactions = orders.count()
    
    # Payment methods breakdown - use invoice totals
    payment_methods = []
    for pm in Order.PAYMENT_METHOD_CHOICES:
        method_orders = orders.filter(payment_method=pm[0])
        count = method_orders.count()
        if count > 0:
            total = 0
            for order in method_orders:
                try:
                    invoice = order.invoice
                    total += invoice.total_amount
                except:
                    items = order.items.all()
                    total += items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
            percentage = (count / total_transactions * 100) if total_transactions > 0 else 0
            payment_methods.append({
                'payment_method': pm[1],
                'count': count,
                'total': total,
                'percentage': percentage
            })
    
    # Pagination
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate accurate totals for each order - use invoice total if exists
    for order in page_obj:
        try:
            invoice = order.invoice
            # Use invoice total (includes GST, discount, etc.)
            order.calculated_total_amount = invoice.total_amount
        except:
            # No invoice, calculate simple total from OrderItems
            items = order.items.all()
            order.calculated_total_amount = items.aggregate(
                total=Sum(F('quantity') * F('price'))
            )['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'period': period,
        'period_choices': PERIOD_CHOICES,
        'status': status,
        'method': method,
        'search': search,
        'total_revenue': total_revenue,
        'success_count': success_count,
        'success_amount': success_amount,
        'pending_count': pending_count,
        'pending_amount': pending_amount,
        'failed_count': failed_count,
        'failed_amount': failed_amount,
        'total_transactions': total_transactions,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'payments/payment_dashboard.html', context)


def payment_detail(request, pk):
    """Detailed view of a single payment transaction"""
    order = get_object_or_404(Order.objects.select_related('customer').prefetch_related('items'), pk=pk)
    items = order.items.all()
    total_items = items.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Check if invoice exists for this order
    try:
        invoice = order.invoice
        # Use invoice total (includes GST, discount, etc.)
        grand_total = invoice.total_amount
        has_invoice = True
        subtotal = invoice.subtotal
        discount = invoice.discount
        tax_amount = invoice.tax_amount
        tax_percentage = invoice.tax_percentage
    except:
        # No invoice, calculate simple total from OrderItems
        grand_total = items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
        has_invoice = False
        subtotal = grand_total
        discount = 0
        tax_amount = 0
        tax_percentage = 0
    
    context = {
        'order': order,
        'items': items,
        'grand_total': grand_total,
        'total_items': total_items,
        'has_invoice': has_invoice,
        'subtotal': subtotal,
        'discount': discount,
        'tax_amount': tax_amount,
        'tax_percentage': tax_percentage,
    }
    
    return render(request, 'payments/payment_detail.html', context)


def invoice(request, pk):
    """Invoice page for an order"""
    order = get_object_or_404(Order.objects.select_related('customer').prefetch_related('items'), pk=pk)
    items = order.items.all()
    grand_total = items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    total_items = items.aggregate(total=Sum('quantity'))['total'] or 0
    
    context = {
        'order': order,
        'items': items,
        'grand_total': grand_total,
        'total_items': total_items,
    }
    
    return render(request, 'orders/invoice.html', context)


def update_payment_status(request, pk):
    """Update payment status via AJAX"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, pk=pk)
            data = json_module.loads(request.body)
            new_status = data.get('status')
            
            if new_status in dict(Order.PAYMENT_STATUS_CHOICES):
                order.payment_status = new_status
                order.save()
                return HttpResponse(
                    json_module.dumps({'success': True}),
                    content_type='application/json'
                )
            else:
                return HttpResponse(
                    json_module.dumps({'success': False, 'error': 'Invalid status'}),
                    content_type='application/json',
                    status=400
                )
        except Exception as e:
            return HttpResponse(
                json_module.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500
            )
    
    return HttpResponse(
        json_module.dumps({'success': False, 'error': 'Invalid request method'}),
        content_type='application/json',
        status=405
    )


def export_payments(request):
    """Export payment report as PDF"""
    period = request.GET.get('period', 'This Year').strip()
    if period not in PERIOD_CHOICES:
        period = 'This Year'
    
    start_dt, end_dt = _get_period_date_range(period)
    orders = Order.objects.select_related('customer').order_by('-order_date')
    
    if start_dt and end_dt:
        orders = orders.filter(order_date__gte=start_dt, order_date__lte=end_dt)
    
    # Generate PDF using reportlab
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Payment Report", title_style))
    elements.append(Paragraph(f"Period: {period}", styles['Normal']))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Summary
    total_revenue = OrderItem.objects.filter(order__in=orders).aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Transactions', str(orders.count())],
        ['Total Revenue', f'₹{total_revenue:,.2f}'],
        ['Successful Payments', str(orders.filter(payment_status='Success').count())],
        ['Pending Payments', str(orders.filter(payment_status='Pending').count())],
        ['Cancelled Payments', str(orders.filter(payment_status='Cancelled').count())],
    ]
    
    from reportlab.lib.units import inch
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Transactions table
    elements.append(Paragraph("Transaction Details", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    transaction_data = [['Order ID', 'Customer', 'Method', 'Amount', 'Status']]
    
    for order in orders[:50]:
        order_total = order.items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
        transaction_data.append([
            order.order_id,
            order.customer.name[:20],
            order.get_payment_method_display(),
            f'₹{order_total:,.2f}',
            order.payment_status
        ])
    
    transaction_table = Table(transaction_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1*inch, 1*inch])
    transaction_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(transaction_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payment_report_{period.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    return response


# --------------------
# SETTINGS PAGE
# --------------------

def settings_page(request):
    """Admin settings page with database persistence."""
    from .models import AppSettings
    from django.contrib.auth import update_session_auth_hash
    
    # Get or create settings
    settings = AppSettings.get_settings()
    
    if request.method == 'POST':
        # General Settings
        settings.store_name = request.POST.get('store_name', settings.store_name)
        settings.contact_email = request.POST.get('contact_email', settings.contact_email)
        settings.contact_phone = request.POST.get('contact_phone', settings.contact_phone)
        settings.store_address = request.POST.get('store_address', settings.store_address)
        settings.currency = request.POST.get('currency', settings.currency)
        settings.timezone = request.POST.get('timezone', settings.timezone)
        settings.language = request.POST.get('language', settings.language)
        
        # Delivery Settings
        settings.delivery_charge_type = request.POST.get('delivery_charge_type', settings.delivery_charge_type)
        settings.delivery_charge = request.POST.get('delivery_charge', settings.delivery_charge)
        settings.min_order_amount = request.POST.get('min_order_amount', settings.min_order_amount)
        settings.free_delivery_limit = request.POST.get('free_delivery_limit', settings.free_delivery_limit)
        settings.delivery_slots = request.POST.get('delivery_slots', settings.delivery_slots)
        settings.service_pincodes = request.POST.get('service_pincodes', settings.service_pincodes)
        
        # Payment Settings
        settings.cod_enabled = 'cod_enabled' in request.POST
        settings.online_payments_enabled = 'online_payments_enabled' in request.POST
        settings.pg_api_key = request.POST.get('pg_api_key', settings.pg_api_key)
        settings.pg_secret_key = request.POST.get('pg_secret_key', settings.pg_secret_key)
        settings.refund_mode = request.POST.get('refund_mode', settings.refund_mode)
        
        # Product Settings
        settings.default_tax = request.POST.get('default_tax', settings.default_tax)
        settings.low_stock_limit = request.POST.get('low_stock_limit', settings.low_stock_limit)
        
        # Notification Settings
        settings.email_notif = 'email_notif' in request.POST
        settings.sms_notif = 'sms_notif' in request.POST
        settings.push_notif = 'push_notif' in request.POST
        settings.whatsapp_api = request.POST.get('whatsapp_api', settings.whatsapp_api)
        
        # Order Settings
        settings.auto_confirm_orders = 'auto_confirm_orders' in request.POST
        settings.order_workflow = request.POST.get('order_workflow', settings.order_workflow)
        settings.cancel_policy = request.POST.get('cancel_policy', settings.cancel_policy)
        
        # SEO Settings
        settings.meta_title = request.POST.get('meta_title', settings.meta_title)
        settings.meta_description = request.POST.get('meta_description', settings.meta_description)
        settings.maintenance_mode = 'maintenance_mode' in request.POST
        settings.analytics_id = request.POST.get('analytics_id', settings.analytics_id)
        
        # Handle file uploads
        if 'store_logo' in request.FILES:
            settings.store_logo = request.FILES['store_logo']
        
        # Save settings
        settings.save()
        
        # Handle password change
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if current_password and new_password and confirm_password:
            if new_password == confirm_password:
                user = request.user
                if user.check_password(current_password):
                    user.set_password(new_password)
                    user.save()
                    # Keep user logged in after password change
                    update_session_auth_hash(request, user)
                    messages.success(request, '✓ Password changed successfully!')
                else:
                    messages.error(request, '✗ Current password is incorrect.')
            else:
                messages.error(request, '✗ New passwords do not match.')
        else:
            messages.success(request, '✓ Settings saved successfully!')
        
        return redirect('settings')
    
    return render(request, 'settings/settings.html', {'settings': settings})


def change_password(request):
    """Simple change password page"""
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if not current_password or not new_password or not confirm_password:
            messages.error(request, '✗ All fields are required.')
        elif new_password != confirm_password:
            messages.error(request, '✗ New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, '✗ Password must be at least 8 characters long.')
        else:
            user = request.user
            if user.check_password(current_password):
                user.set_password(new_password)
                user.save()
                # Keep user logged in after password change
                update_session_auth_hash(request, user)
                messages.success(request, '✓ Password changed successfully!')
                return redirect('dashboard')
            else:
                messages.error(request, '✗ Current password is incorrect.')
    
    return render(request, 'change_password.html')


def home(request):
    from store.models import Offer, Batch
    from django.utils import timezone
    
    products_queryset = Product.objects.all().prefetch_related('variants')
    
    # Get valid offers (active and within date range)
    today = timezone.now().date()
    valid_offers = Offer.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).prefetch_related('products', 'categories')
    
    # Apply offers to products
    products_with_offers = []
    for product in products_queryset:
        # Calculate display price from cheapest variant
        first_variant = product.variants.filter(is_active=True).order_by('price').first()
        if first_variant:
            product.calculated_display_price = first_variant.price
            base_price = float(first_variant.price)
        else:
            product.calculated_display_price = product.selling_price
            base_price = float(product.selling_price)
        
        # Initialize offer attributes
        product.final_price = base_price
        product.discount_percentage = 0
        product.offer_name = None
        
        # Check if product has any valid offer
        best_discount = 0
        best_offer = None
        
        for offer in valid_offers:
            # Check if offer applies to this product
            applies = False
            
            # Check if product is directly in offer
            if offer.products.filter(id=product.id).exists():
                applies = True
            
            # Check if product's category is in offer
            if product.category and offer.categories.filter(id=product.category.id).exists():
                applies = True
            
            if applies:
                # Calculate discount
                if offer.discount_type == 'percentage':
                    discount = float(offer.discount_value)
                    if discount > best_discount:
                        best_discount = discount
                        best_offer = offer
                elif offer.discount_type == 'fixed':
                    # Convert fixed amount to percentage for comparison
                    discount_amount = float(offer.discount_value)
                    discount_percentage = (discount_amount / base_price) * 100
                    if discount_percentage > best_discount:
                        best_discount = discount_percentage
                        best_offer = offer
        
        # Apply best discount
        if best_offer:
            if best_offer.discount_type == 'percentage':
                discount_amount = (base_price * float(best_offer.discount_value)) / 100
                product.final_price = base_price - discount_amount
                product.discount_percentage = float(best_offer.discount_value)
            elif best_offer.discount_type == 'fixed':
                product.final_price = base_price - float(best_offer.discount_value)
                product.discount_percentage = ((float(best_offer.discount_value) / base_price) * 100)
            
            product.offer_name = best_offer.name
        
        products_with_offers.append(product)
    
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()

    context = {
        'products': products_with_offers,
        'categories': categories,
        'subcategories': subcategories
    }

    return render(request, 'store/home.html', context)



# SMS OTP Functions
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import random

# In-memory OTP storage (use Redis in production)
otp_storage = {}

@csrf_exempt
def send_otp_api(request):
    """Send OTP to mobile number"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mobile = data.get('mobile', '').strip()
            
            # Validate mobile
            if not mobile or len(mobile) != 10 or not mobile.isdigit():
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid mobile number'
                }, status=400)
            
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            
            # Store OTP
            otp_storage[mobile] = {
                'otp': otp,
                'timestamp': datetime.now(),
                'attempts': 0
            }
            
            # Send SMS via MSG91
            import requests
            
            # MSG91 Configuration
            AUTH_KEY = "496168Ax9t0Id5Isgc699d699aP1"  # Your MSG91 Auth Key
            TEMPLATE_ID = "699d3d8eaf751c807f0796f2"  # Your approved template ID
            
            try:
                url = "https://control.msg91.com/api/v5/otp"
                payload = {
                    "template_id": TEMPLATE_ID,
                    "mobile": f"91{mobile}",
                    "authkey": AUTH_KEY,
                    "otp": otp
                }
                headers = {
                    "Content-Type": "application/json"
                }
                response = requests.post(url, json=payload, headers=headers)
                print(f"📱 MSG91 Response: {response.status_code} - {response.text}")
                
                if response.status_code != 200:
                    print(f"⚠️ MSG91 Error: {response.text}")
            except Exception as sms_error:
                print(f"❌ SMS Error: {str(sms_error)}")
            
            # For demo: Log OTP (remove in production)
            print(f"📱 OTP for {mobile}: {otp}")
            
            return JsonResponse({
                'success': True,
                'message': f'OTP sent to +91 {mobile}'
                # OTP not sent in response for security
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def verify_otp_api(request):
    """Verify OTP"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mobile = data.get('mobile', '').strip()
            entered_otp = data.get('otp', '').strip()
            
            if mobile not in otp_storage:
                return JsonResponse({
                    'success': False,
                    'message': 'No OTP found'
                }, status=400)
            
            stored_data = otp_storage[mobile]
            
            # Check expiry (30 seconds)
            if datetime.now() - stored_data['timestamp'] > timedelta(seconds=30):
                del otp_storage[mobile]
                return JsonResponse({
                    'success': False,
                    'message': 'OTP expired'
                }, status=400)
            
            # Check attempts
            if stored_data['attempts'] >= 3:
                del otp_storage[mobile]
                return JsonResponse({
                    'success': False,
                    'message': 'Too many attempts'
                }, status=400)
            
            # Verify OTP
            if entered_otp == stored_data['otp']:
                del otp_storage[mobile]
                return JsonResponse({
                    'success': True,
                    'message': 'OTP verified'
                })
            else:
                stored_data['attempts'] += 1
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid OTP. {3 - stored_data["attempts"]} attempts remaining'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


# Email OTP Functions
@csrf_exempt
def send_email_otp_api(request):
    """Send OTP to email address"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            
            # Validate email
            import re
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not email or not re.match(email_regex, email):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid email address'
                }, status=400)
            
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            
            # Store OTP
            otp_storage[email] = {
                'otp': otp,
                'timestamp': datetime.now(),
                'attempts': 0
            }
            
            # Send Email
            try:
                subject = 'Your OTP for Password Reset - The Daily Grocer'
                message = f'''
Hello,

Your OTP for password reset is: {otp}

This OTP is valid for 30 seconds only.

Do not share this OTP with anyone.

If you did not request this, please ignore this email.

Thank you,
The Daily Grocer Team
                '''
                
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [email]
                
                send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    fail_silently=False,
                )
                
                print(f"📧 Email OTP sent to {email}: {otp}")
                
                return JsonResponse({
                    'success': True,
                    'message': f'OTP sent to {email}'
                    # OTP not sent in response for security
                })
                
            except Exception as email_error:
                print(f"❌ Email Error: {str(email_error)}")
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to send email'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def verify_email_otp_api(request):
    """Verify Email OTP"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            entered_otp = data.get('otp', '').strip()
            
            if email not in otp_storage:
                return JsonResponse({
                    'success': False,
                    'message': 'No OTP found'
                }, status=400)
            
            stored_data = otp_storage[email]
            
            # Check expiry (30 seconds)
            if datetime.now() - stored_data['timestamp'] > timedelta(seconds=30):
                del otp_storage[email]
                return JsonResponse({
                    'success': False,
                    'message': 'OTP expired'
                }, status=400)
            
            # Check attempts
            if stored_data['attempts'] >= 3:
                del otp_storage[email]
                return JsonResponse({
                    'success': False,
                    'message': 'Too many attempts'
                }, status=400)
            
            # Verify OTP
            if entered_otp == stored_data['otp']:
                del otp_storage[email]
                return JsonResponse({
                    'success': True,
                    'message': 'OTP verified'
                })
            else:
                stored_data['attempts'] += 1
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid OTP. {3 - stored_data["attempts"]} attempts remaining'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
