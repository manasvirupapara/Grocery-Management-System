from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category,
    SubCategory,
    Offer,
    AppSettings,
    Order,
    OrderItem,
    Product,
    ProductImage,
    ProductVariant,
    Batch,
    Tax,
    Invoice,
    InvoiceItem,
)
from customers.models import Customer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("name", "category__name")


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("name", "discount_type", "discount_value", "start_date", "end_date", "is_active")
    list_filter = ("is_active", "discount_type", "start_date", "end_date")
    search_fields = ("name", "description")
    filter_horizontal = ("products", "categories")


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ("store_name", "contact_email", "contact_phone", "updated_at")
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not AppSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deleting settings
        return False


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "customer", "order_date", "payment_status", "payment_method", "total_items", "total_amount")
    list_filter = ("payment_status", "payment_method", "order_date")
    search_fields = ("order_id", "customer__name", "customer__email")
    inlines = [OrderItemInline]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "location", "gender")
    search_fields = ("name", "email", "phone")


# Product Variant Inline
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['weight', 'price', 'cost_price', 'stock', 'low_stock_alert', 'expiry_date', 'stock_status_display', 'is_active']
    readonly_fields = ['stock_status_display']
    
    def stock_status_display(self, obj):
        """Display stock status with color coding"""
        if not obj.pk:
            return '-'
        
        if obj.stock == 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">OUT OF STOCK</span>'
            )
        elif obj.stock <= obj.low_stock_alert:
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">LOW STOCK ({} left)</span>',
                obj.stock
            )
        else:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">IN STOCK ({} available)</span>',
                obj.stock
            )
    stock_status_display.short_description = 'Status'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "variant_count", "stock_quantity", "low_stock_threshold", "cost_price", "selling_price", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("name", "sku")
    inlines = [ProductVariantInline]
    
    def variant_count(self, obj):
        """Display number of variants"""
        count = obj.variants.count()
        if count == 0:
            return format_html('<span style="color: #999;">No variants</span>')
        return format_html('<span style="color: #28a745; font-weight: bold;">{} variants</span>', count)
    variant_count.short_description = 'Variants'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "created_at")
    list_filter = ("is_primary", "created_at")
    search_fields = ("product__name",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "weight", "price", "stock", "low_stock_alert", "expiry_date", "status_badge", "is_active")
    list_filter = ("is_active", "product__category")
    search_fields = ("product__name", "weight")
    list_editable = ("price", "stock", "is_active")
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        if obj.stock == 0:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">OUT OF STOCK</span>'
            )
        elif obj.stock <= obj.low_stock_alert:
            return format_html(
                '<span style="background: #ffc107; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">LOW STOCK</span>'
            )
        else:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">IN STOCK</span>'
            )
    status_badge.short_description = 'Status'
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'weight')
        }),
        ('Pricing', {
            'fields': ('price', 'cost_price')
        }),
        ('Stock Management', {
            'fields': ('stock', 'low_stock_alert', 'expiry_date')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "product", "manufacturing_date", "expiry_date", "quantity", "cost_price", "is_expired", "days_until_expiry", "created_at")
    list_filter = ("manufacturing_date", "expiry_date", "product__category")
    search_fields = ("batch_number", "product__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("manufacturing_date", "created_at")
    
    fieldsets = (
        ("Batch Information", {
            "fields": ("product", "batch_number", "manufacturing_date", "expiry_date")
        }),
        ("Inventory", {
            "fields": ("quantity", "cost_price")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def is_expired(self, obj):
        """Display if batch is expired"""
        if obj.is_expired():
            return "❌ Expired"
        return "✅ Active"
    is_expired.short_description = "Status"
    
    def days_until_expiry(self, obj):
        """Display days until expiry"""
        days = obj.days_until_expiry()
        if days is None:
            return "-"
        if days < 0:
            return f"Expired {abs(days)} days ago"
        if days == 0:
            return "⚠️ Expires today"
        if days <= 7:
            return f"⚠️ {days} days"
        if days <= 30:
            return f"🟡 {days} days"
        return f"✅ {days} days"
    days_until_expiry.short_description = "Days to Expiry"
    
    def save_model(self, request, obj, form, change):
        """Update product stock when batch is saved"""
        super().save_model(request, obj, form, change)
        # Update product total stock
        product = obj.product
        product.stock_quantity = Batch.get_total_stock(product)
        product.save()
    
    def delete_model(self, request, obj):
        """Update product stock when batch is deleted"""
        product = obj.product
        super().delete_model(request, obj)
        # Update product total stock
        product.stock_quantity = Batch.get_total_stock(product)
        product.save()


@admin.action(description="Set selected tax as active (others inactive)")
def make_tax_active(modeladmin, request, queryset):
    # Activate only the first selected tax
    tax = queryset.first()
    if tax:
        Tax.objects.update(is_active=False)
        tax.is_active = True
        tax.save(update_fields=["is_active"])


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("tax_name", "tax_percentage", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("tax_name",)
    actions = [make_tax_active]


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ("product_name", "quantity", "unit_price")
    can_delete = False


@admin.action(description="Mark selected invoices as Paid")
def mark_invoice_paid(modeladmin, request, queryset):
    queryset.update(payment_status="Paid")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "order", "customer", "issue_date", "payment_status", "subtotal", "discount", "tax_amount", "total_amount")
    list_filter = ("payment_status", "issue_date")
    search_fields = ("invoice_number", "order__order_id", "customer__name", "transaction_id")
    readonly_fields = ("invoice_number", "order", "customer", "subtotal", "tax_amount", "total_amount", "tax_name", "tax_percentage", "transaction_id", "issue_date")
    inlines = [InvoiceItemInline]
    actions = [mark_invoice_paid]