"""
Admin Configuration for Product Variant System
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductVariant


class ProductVariantInline(admin.TabularInline):
    """
    Inline admin for managing product variants within Product admin
    """
    model = ProductVariant
    extra = 1
    fields = [
        'weight', 
        'price', 
        'cost_price', 
        'stock', 
        'low_stock_alert', 
        'status_display',
        'is_active',
        'sku'
    ]
    readonly_fields = ['status_display']
    
    def status_display(self, obj):
        """Display status with color coding"""
        if obj.pk:  # Only for saved objects
            color = obj.get_status_display_color()
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color,
                obj.get_status_display()
            )
        return '-'
    status_display.short_description = 'Status'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product with inline variants
    """
    list_display = [
        'name', 
        'category', 
        'variant_count',
        'price_range_display',
        'total_stock_display',
        'stock_status_display',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'image')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def variant_count(self, obj):
        """Display number of variants"""
        count = obj.variants.count()
        active_count = obj.variants.filter(is_active=True).count()
        return f"{active_count}/{count}"
    variant_count.short_description = 'Variants (Active/Total)'
    
    def price_range_display(self, obj):
        """Display price range across variants"""
        min_price, max_price = obj.get_price_range()
        if min_price is None:
            return '-'
        if min_price == max_price:
            return f"₹{min_price}"
        return f"₹{min_price} - ₹{max_price}"
    price_range_display.short_description = 'Price Range'
    
    def total_stock_display(self, obj):
        """Display total stock across all variants"""
        total = obj.total_stock()
        if total == 0:
            return format_html('<span style="color: #dc3545;">0</span>')
        elif total <= 20:
            return format_html('<span style="color: #ffc107;">{}</span>', total)
        return format_html('<span style="color: #28a745;">{}</span>', total)
    total_stock_display.short_description = 'Total Stock'
    
    def stock_status_display(self, obj):
        """Display overall stock status"""
        if not obj.has_stock():
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">OUT OF STOCK</span>'
            )
        
        low_stock_variants = obj.variants.filter(
            stock__gt=0, 
            stock__lte=models.F('low_stock_alert')
        ).count()
        
        if low_stock_variants > 0:
            return format_html(
                '<span style="background: #ffc107; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">LOW STOCK</span>'
            )
        
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">IN STOCK</span>'
        )
    stock_status_display.short_description = 'Status'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    Standalone admin for Product Variants
    """
    list_display = [
        'product',
        'weight',
        'price',
        'cost_price',
        'stock',
        'low_stock_alert',
        'status_badge',
        'is_active',
        'sku'
    ]
    list_filter = ['status', 'is_active', 'product__category']
    search_fields = ['product__name', 'weight', 'sku']
    readonly_fields = ['status', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'weight', 'sku')
        }),
        ('Pricing', {
            'fields': ('price', 'cost_price')
        }),
        ('Stock Management', {
            'fields': ('stock', 'low_stock_alert', 'status')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        color = obj.get_status_display_color()
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'
    
    actions = ['mark_as_active', 'mark_as_inactive', 'reset_low_stock_alert']
    
    def mark_as_active(self, request, queryset):
        """Bulk action to mark variants as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} variant(s) marked as active.')
    mark_as_active.short_description = 'Mark selected as active'
    
    def mark_as_inactive(self, request, queryset):
        """Bulk action to mark variants as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} variant(s) marked as inactive.')
    mark_as_inactive.short_description = 'Mark selected as inactive'
    
    def reset_low_stock_alert(self, request, queryset):
        """Bulk action to reset low stock alert to 10"""
        updated = queryset.update(low_stock_alert=10)
        self.message_user(request, f'{updated} variant(s) low stock alert reset to 10.')
    reset_low_stock_alert.short_description = 'Reset low stock alert to 10'
