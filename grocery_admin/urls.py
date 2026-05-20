from django.contrib import admin
from django.urls import path,include
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from store import views
from store import api_views  # Import API views
from store import google_auth  # Google OAuth views
from django.conf import settings
from django.conf.urls.static import static
import batch_views  # Import batch views


def get_product_expiry_date(product_obj):
    """Get nearest expiry date from available batches"""
    from store.models import Batch
    from django.utils import timezone
    
    nearest_batch = product_obj.batches.filter(
        quantity__gt=0,
        expiry_date__gte=timezone.now().date()
    ).order_by('expiry_date').first()
    
    return nearest_batch.expiry_date if nearest_batch else product_obj.expiry_date

def home(request):
    from store.models import Category, SubCategory, Product, Offer, Tax, Batch
    from django.utils import timezone
    from decimal import Decimal
    
    # Get all active categories with their subcategories
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
    
    # Get all active products with their categories
    products_queryset = Product.objects.filter(is_active=True).select_related('category', 'subcategory').prefetch_related('images')
    
    # Get active tax
    active_tax = Tax.get_active()
    
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
        # Create a custom object that has both original attributes and new ones
        class ProductWithOffer:
            def __init__(self, product_obj):
                self.id = product_obj.id
                self.name = product_obj.name
                # Minimum variant price use karo
                _variants = product_obj.variants.filter(is_active=True).order_by('price')
                _min_v = _variants.first()
                _base = float(_min_v.price) if _min_v else float(product_obj.selling_price)
                self.selling_price = _base
                self.price = _base
                self.original_price = _base
                self.cost_price = product_obj.cost_price
                # Get stock from batches using FIFO
                self.stock_quantity = Batch.get_total_stock(product_obj)
                self.low_stock_threshold = product_obj.low_stock_threshold
                self.category = product_obj.category
                self.subcategory = product_obj.subcategory
                self.image = product_obj.image.url if product_obj.image else None
                self.images = product_obj.images  # Add images relationship
                self.description = product_obj.description  # Add description
                self.is_active = product_obj.is_active
                self.sku = product_obj.sku
                self.expiry_date = get_product_expiry_date(product_obj)
                self.discount_percentage = 0
                self.offer_name = None
                self.final_price = _base
                first_variant = product_obj.variants.first()
                self.unit_type = first_variant.unit_type if first_variant else 'units'
        
        product_data = ProductWithOffer(product)
        
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
                    discount_percentage = (discount_amount / float(product.selling_price)) * 100
                    if discount_percentage > best_discount:
                        best_discount = discount_percentage
                        best_offer = offer
        
        # Apply best discount
        if best_offer:
            if best_offer.discount_type == 'percentage':
                discount_amount = (product_data.original_price * float(best_offer.discount_value)) / 100
                product_data.final_price = product_data.original_price - discount_amount
                product_data.discount_percentage = float(best_offer.discount_value)
            elif best_offer.discount_type == 'fixed':
                product_data.final_price = product_data.original_price - float(best_offer.discount_value)
                product_data.discount_percentage = ((float(best_offer.discount_value) / product_data.original_price) * 100)
            
            product_data.offer_name = best_offer.name
        
        products_with_offers.append(product_data)
    
    context = {
        'categories': categories,
        'products': products_with_offers,
        'active_tax': active_tax,
        'tax_percentage': float(active_tax.tax_percentage) if active_tax else 0,
        'tax_name': active_tax.tax_name if active_tax else 'Tax',
    }
    return render(request, 'store/home.html', context)

def cart_page(request):
    return render(request, 'store/cart.html')

def wishlist_page(request):
    return render(request, 'store/wishlist.html')

def auth_page(request):
    return render(request, 'store/auth.html')

def profile_page(request):
    return render(request, 'store/profile.html')

def customer_settings_page(request):
    return render(request, 'store/settings.html')

def checkout_page(request):
    from store.models import Tax
    
    # Get active tax
    active_tax = Tax.get_active()
    
    context = {
        'active_tax': active_tax,
        'tax_percentage': float(active_tax.tax_percentage) if active_tax else 0,
        'tax_name': active_tax.tax_name if active_tax else 'Tax',
    }
    return render(request, 'store/checkout.html', context)

def shop_page(request):
    from store.models import Category, SubCategory, Product, Offer, Tax, Batch
    from django.utils import timezone
    
    # Get all active categories with their subcategories
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
    
    # Get all active products with their categories
    products_queryset = Product.objects.filter(is_active=True).select_related('category', 'subcategory').prefetch_related('images')
    
    # Get active tax
    active_tax = Tax.get_active()
    
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
        # Create a custom object that has both original attributes and new ones
        class ProductWithOffer:
            def __init__(self, product_obj):
                self.id = product_obj.id
                self.name = product_obj.name
                # Minimum variant price use karo
                _variants = product_obj.variants.filter(is_active=True).order_by('price')
                _min_v = _variants.first()
                _base = float(_min_v.price) if _min_v else float(product_obj.selling_price)
                self.selling_price = _base
                self.price = _base
                self.original_price = _base
                self.cost_price = product_obj.cost_price
                # Get stock from batches using FIFO
                self.stock_quantity = Batch.get_total_stock(product_obj)
                self.low_stock_threshold = product_obj.low_stock_threshold
                self.category = product_obj.category
                self.subcategory = product_obj.subcategory
                self.image = product_obj.image.url if product_obj.image else None
                self.images = product_obj.images  # Add images relationship
                self.description = product_obj.description  # Add description
                self.is_active = product_obj.is_active
                self.sku = product_obj.sku
                self.expiry_date = get_product_expiry_date(product_obj)
                self.discount_percentage = 0
                self.offer_name = None
                self.final_price = _base
                first_variant = product_obj.variants.first()
                self.unit_type = first_variant.unit_type if first_variant else 'units'
        
        product_data = ProductWithOffer(product)
        
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
                    discount_percentage = (discount_amount / float(product.selling_price)) * 100
                    if discount_percentage > best_discount:
                        best_discount = discount_percentage
                        best_offer = offer
        
        # Apply best discount
        if best_offer:
            if best_offer.discount_type == 'percentage':
                discount_amount = (product_data.original_price * float(best_offer.discount_value)) / 100
                product_data.final_price = product_data.original_price - discount_amount
                product_data.discount_percentage = float(best_offer.discount_value)
            elif best_offer.discount_type == 'fixed':
                product_data.final_price = product_data.original_price - float(best_offer.discount_value)
                product_data.discount_percentage = ((float(best_offer.discount_value) / product_data.original_price) * 100)
            
            product_data.offer_name = best_offer.name
        
        products_with_offers.append(product_data)
    
    context = {
        'categories': categories,
        'products': products_with_offers,
        'active_tax': active_tax,
        'tax_percentage': float(active_tax.tax_percentage) if active_tax else 0,
        'tax_name': active_tax.tax_name if active_tax else 'Tax',
        'search_query': request.GET.get('search', ''),
    }
    return render(request, 'store/shop.html', context)

def about_page(request):
    return render(request, 'store/about.html')

def contact_page(request):
    return render(request, 'store/contact.html')

def delivery_page(request):
    return render(request, 'store/delivery.html')

def invoice_page(request):
    return render(request, 'store/lnvoice.html')

def cancel_order_page(request):
    return render(request, 'store/cancel order.html')

def orders_page(request):
    return render(request, 'store/orders.html')

def addresses_page(request):
    return render(request, 'store/addresses.html')

def search_page(request):
    from store.models import Product, Tax
    
    search_query = request.GET.get('q', '')
    
    # Get all active products
    products_queryset = Product.objects.filter(is_active=True).select_related('category', 'subcategory').prefetch_related('images')
    
    # Filter by search query if provided
    if search_query:
        products_queryset = products_queryset.filter(name__icontains=search_query)
    
    # Get active tax
    active_tax = Tax.get_active()
    
    # Convert to list with offer data (reuse same logic as home/shop)
    from django.utils import timezone
    from store.models import Offer
    
    today = timezone.now().date()
    valid_offers = Offer.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).prefetch_related('products', 'categories')
    
    products_with_offers = []
    for product in products_queryset:
        class ProductWithOffer:
            def __init__(self, product_obj):
                self.id = product_obj.id
                self.name = product_obj.name
                self.selling_price = product_obj.selling_price
                self.price = product_obj.selling_price
                self.original_price = float(product_obj.selling_price)
                self.cost_price = product_obj.cost_price
                self.stock_quantity = product_obj.stock_quantity
                self.low_stock_threshold = product_obj.low_stock_threshold
                self.category = product_obj.category
                self.subcategory = product_obj.subcategory
                self.image = product_obj.image.url if product_obj.image else None
                self.images = product_obj.images
                self.description = product_obj.description
                self.is_active = product_obj.is_active
                self.sku = product_obj.sku
                self.expiry_date = get_product_expiry_date(product_obj)
                self.discount_percentage = 0
                self.offer_name = None
                self.final_price = _base
                first_variant = product_obj.variants.first()
                self.unit_type = first_variant.unit_type if first_variant else 'units'
        
        product_data = ProductWithOffer(product)
        
        # Apply offers (same logic as home/shop)
        best_discount = 0
        best_offer = None
        
        for offer in valid_offers:
            applies = False
            if offer.products.filter(id=product.id).exists():
                applies = True
            if product.category and offer.categories.filter(id=product.category.id).exists():
                applies = True
            
            if applies:
                if offer.discount_type == 'percentage':
                    discount = float(offer.discount_value)
                    if discount > best_discount:
                        best_discount = discount
                        best_offer = offer
                elif offer.discount_type == 'fixed':
                    discount_amount = float(offer.discount_value)
                    discount_percentage = (discount_amount / float(product.selling_price)) * 100
                    if discount_percentage > best_discount:
                        best_discount = discount_percentage
                        best_offer = offer
        
        if best_offer:
            if best_offer.discount_type == 'percentage':
                discount_amount = (product_data.original_price * float(best_offer.discount_value)) / 100
                product_data.final_price = product_data.original_price - discount_amount
                product_data.discount_percentage = float(best_offer.discount_value)
            elif best_offer.discount_type == 'fixed':
                product_data.final_price = product_data.original_price - float(best_offer.discount_value)
                product_data.discount_percentage = ((float(best_offer.discount_value) / product_data.original_price) * 100)
            
            product_data.offer_name = best_offer.name
        
        products_with_offers.append(product_data)
    
    context = {
        'products': products_with_offers,
        'search_query': search_query,
        'results_count': len(products_with_offers),
        'tax_percentage': float(active_tax.tax_percentage) if active_tax else 0,
        'tax_name': active_tax.tax_name if active_tax else 'Tax',
    }
    return render(request, 'store/search.html', context)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('shop/', shop_page, name='shop'),
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    path('delivery/', delivery_page, name='delivery'),
    path('invoice/', invoice_page, name='invoice'),
    path('cancel-order/', cancel_order_page, name='cancel_order'),
    path('orders/', orders_page, name='orders'),
    path('addresses/', addresses_page, name='addresses'),
    path('cart/', cart_page, name='cart'),
    path('wishlist/', wishlist_page, name='wishlist'),
    path('auth/', auth_page, name='auth'),
    path('auth/google/', google_auth.google_login_redirect, name='google_login'),
    path('auth/google/callback/', google_auth.google_callback, name='google_callback'),
    path('auth/google/clear-session/', google_auth.google_clear_session, name='google_clear_session'),
    path('profile/', profile_page, name='profile'),
    path('settings/', customer_settings_page, name='settings'),
    path('checkout/', checkout_page, name='checkout'),
    path('login/', views.admin_login, name='login'),
    
    # Cart & Inventory API - Direct paths (not through store/)
    path('api/cart/add/', api_views.add_to_cart_api, name='api_add_to_cart'),
    path('api/cart/remove/', api_views.remove_from_cart_api, name='api_remove_from_cart'),
    path('api/cart/update-quantity/', api_views.update_cart_quantity_api, name='api_update_cart_quantity'),
    path('api/product/<int:product_id>/stock/', api_views.get_product_stock, name='api_get_product_stock'),
    path('api/product/<int:product_id>/variants/', api_views.get_product_with_variants, name='api_get_product_variants'),
    path('api/order/create/', api_views.create_order_api, name='api_create_order'),
    path('api/invoice/<str:order_id>/', api_views.get_invoice_api, name='api_get_invoice'),
    
    # Store admin URLs
    path('store/', include('store.urls')),
    
    # Batch Management URLs
    path('batches/', batch_views.batch_list, name='batch_list'),
    path('batches/add/', batch_views.batch_add, name='batch_add'),
    path('batches/edit/<int:batch_id>/', batch_views.batch_edit, name='batch_edit'),
    path('batches/delete/<int:batch_id>/', batch_views.batch_delete, name='batch_delete'),
    
    # OTP APIs
    path('api/send-otp/', views.send_otp_api, name='send_otp'),
    path('api/verify-otp/', views.verify_otp_api, name='verify_otp'),
    path('api/send-email-otp/', views.send_email_otp_api, name='send_email_otp'),
    path('api/verify-email-otp/', views.verify_email_otp_api, name='verify_email_otp'),

    # FORGOT PASSWORD FLOW (FULL)
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='forgot_password.html'
    ), name='password_reset'),

    path('forgot-password-done/', auth_views.PasswordResetDoneView.as_view(
        template_name='forgot_password_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('reset-done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),

    path('customers/', include('customers.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

