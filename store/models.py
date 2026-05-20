from django.db import models
from customers.models import Customer
import uuid
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=10, default='box', blank=True, help_text='Emoji icon for category')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class SubCategory(models.Model):
    """Sub-category under a main category"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='subcategories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Sub Categories'
        ordering = ['name']
        unique_together = [['category', 'name']]  # Same name not allowed within same category
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Offer(models.Model):
    """Offers and Discounts"""
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Optional: Apply to specific products or categories
    products = models.ManyToManyField('Product', blank=True, related_name='offers')
    categories = models.ManyToManyField(Category, blank=True, related_name='offers')
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def is_valid(self):
        """Check if offer is currently valid"""
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date


class AppSettings(models.Model):
    """Application Settings - Single row table"""
    # General Settings
    store_name = models.CharField(max_length=200, default='Grocery Admin')
    store_logo = models.ImageField(upload_to='settings/', blank=True, null=True)
    contact_email = models.EmailField(default='admin@example.com')
    contact_phone = models.CharField(max_length=20, default='+91 00000 00000')
    store_address = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=10, default='INR')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    language = models.CharField(max_length=10, default='en')
    
    # Delivery Settings
    delivery_charge_type = models.CharField(max_length=20, default='fixed')
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=40)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=199)
    free_delivery_limit = models.DecimalField(max_digits=10, decimal_places=2, default=999)
    delivery_slots = models.TextField(blank=True, null=True)
    service_pincodes = models.TextField(blank=True, null=True)
    
    # Payment Settings
    cod_enabled = models.BooleanField(default=True)
    online_payments_enabled = models.BooleanField(default=True)
    pg_api_key = models.CharField(max_length=200, blank=True, null=True)
    pg_secret_key = models.CharField(max_length=200, blank=True, null=True)
    refund_mode = models.CharField(max_length=20, default='manual')
    
    # Product Settings
    default_tax = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    low_stock_limit = models.IntegerField(default=10)
    
    # Notification Settings
    email_notif = models.BooleanField(default=True)
    sms_notif = models.BooleanField(default=False)
    push_notif = models.BooleanField(default=False)
    whatsapp_api = models.CharField(max_length=200, blank=True, null=True)
    
    # Order Settings
    auto_confirm_orders = models.BooleanField(default=True)
    order_workflow = models.TextField(blank=True, null=True)
    cancel_policy = models.TextField(blank=True, null=True)
    
    # SEO Settings
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    maintenance_mode = models.BooleanField(default=False)
    analytics_id = models.CharField(max_length=50, blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'App Settings'
        verbose_name_plural = 'App Settings'
    
    def __str__(self):
        return f"Settings - {self.store_name}"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


# --------------------
# PRODUCT / INVENTORY MODEL
# --------------------
class Product(models.Model):
    """Minimal product model to support inventory + reporting."""
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=80, blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # Main image

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    # Expiry Date
    expiry_date = models.DateField(blank=True, null=True)

    # Pricing (for Profit & Loss)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name
    
    @property
    def display_price(self):
        """
        Get display price from first variant
        Returns first variant's price, or product selling_price as fallback
        """
        first_variant = self.variants.filter(is_active=True).order_by('price').first()
        if first_variant:
            return first_variant.price
        return self.selling_price
    
    def get_display_price(self):
        """Backward compatibility - calls display_price property"""
        return self.display_price
    
    def get_display_unit(self, quantity=None):
        """
        Get display unit text from most common/largest variant's unit_type
        Prioritizes kg over g, liters over ml, etc.
        Returns: 'kg', 'g', 'pieces', 'liters', etc.
        """
        variants = self.variants.filter(is_active=True)
        if not variants.exists():
            return ' units'  # Default fallback with space
        
        # Priority order: kg > l > piece > pack > box > g > ml
        priority_order = ['kg', 'l', 'piece', 'pack', 'box', 'g', 'ml']
        
        # Get all unit types from variants
        unit_types = list(variants.values_list('unit_type', flat=True).distinct())
        
        # Find the highest priority unit type
        selected_unit = None
        for unit in priority_order:
            if unit in unit_types:
                selected_unit = unit
                break
        
        # Fallback to first variant's unit if no match
        if not selected_unit:
            selected_unit = variants.first().unit_type
        
        if quantity is None:
            quantity = self.stock_quantity
        
        unit_map = {
            'kg': 'kg',
            'g': 'g',
            'l': ' liter' if quantity == 1 else ' liters',
            'ml': 'ml',
            'piece': ' piece' if quantity == 1 else ' pieces',
            'pack': ' pack' if quantity == 1 else ' packs',
            'box': ' box' if quantity == 1 else ' boxes',
        }
        return unit_map.get(selected_unit, ' units')

    def is_expired(self):
        """Check if product is expired"""
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date < timezone.now().date()
        return False

    def days_until_expiry(self):
        """Get days remaining until expiry"""
        if self.expiry_date:
            from django.utils import timezone
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None


class ProductImage(models.Model):
    """Multiple images for a product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - Image"


# --------------------
# PRODUCT VARIANT MODEL
# --------------------
class ProductVariant(models.Model):
    """
    Product Variant Model - Different weight/size options for a product
    Each product can have multiple variants with different weights, prices, and stock
    """
    
    UNIT_TYPE_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('piece', 'Piece'),
        ('pack', 'Pack'),
        ('box', 'Box'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    # Variant details
    weight = models.CharField(
        max_length=50,
        help_text="e.g., 100g, 250g, 500g, 1kg, 5kg"
    )
    
    # Unit type for display
    unit_type = models.CharField(
        max_length=10,
        choices=UNIT_TYPE_CHOICES,
        default='kg',
        help_text="Unit type for stock display (e.g., kg, piece, liter)"
    )
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Stock management
    stock = models.IntegerField(default=0)
    low_stock_alert = models.IntegerField(default=10)
    
    # Expiry
    expiry_date = models.DateField(blank=True, null=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['product', 'weight']
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        unique_together = ['product', 'weight']
    
    def __str__(self):
        return f"{self.product.name} - {self.weight}"
    
    def get_unit_display_text(self, quantity):
        """
        Get proper unit display text based on unit_type and quantity
        Examples:
        - 15 kg available
        - 10 pieces available
        - 5 liters available
        """
        unit_map = {
            'kg': 'kg',
            'g': 'g',
            'l': 'liter' if quantity == 1 else 'liters',
            'ml': 'ml',
            'piece': 'piece' if quantity == 1 else 'pieces',
            'pack': 'pack' if quantity == 1 else 'packs',
            'box': 'box' if quantity == 1 else 'boxes',
        }
        unit_text = unit_map.get(self.unit_type, 'units')
        return f"{quantity} {unit_text} available"
    
    def is_in_stock(self):
        """Check if variant is in stock"""
        return self.stock > 0
    
    def is_low_stock(self):
        """Check if variant is low on stock"""
        return 0 < self.stock <= self.low_stock_alert
    
    def is_out_of_stock(self):
        """Check if variant is out of stock"""
        return self.stock == 0
    
    def get_status(self):
        """Get stock status"""
        if self.stock == 0:
            return 'out_of_stock'
        elif self.stock <= self.low_stock_alert:
            return 'low_stock'
        else:
            return 'in_stock'


# --------------------    class Meta:
        ordering = ['-is_primary', '-created_at']


# BATCH MANAGEMENT MODEL
# --------------------
class Batch(models.Model):
    """Batch model for tracking product inventory with FIFO method."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100, unique=True)
    manufacturing_date = models.DateField()
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['manufacturing_date', 'created_at']  # FIFO ordering
        verbose_name_plural = "Batches"

    def __str__(self):
        return f"{self.product.name} - Batch {self.batch_number}"

    def is_expired(self):
        """Check if batch is expired"""
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()

    def days_until_expiry(self):
        """Get days remaining until expiry"""
        from django.utils import timezone
        delta = self.expiry_date - timezone.now().date()
        return delta.days

    def is_available(self):
        """Check if batch has available quantity"""
        return self.quantity > 0 and not self.is_expired()

    def save(self, *args, **kwargs):
        """Override save to update Product fields when batch is added/updated"""
        super().save(*args, **kwargs)
        
        # Update product stock_quantity (sum of all batch quantities)
        total_stock = sum(
            batch.quantity for batch in self.product.batches.all()
        )
        self.product.stock_quantity = total_stock
        
        # Update product expiry_date (earliest expiry from available batches)
        available_batches = self.product.batches.filter(
            quantity__gt=0
        ).exclude(
            expiry_date__lt=timezone.now().date()
        ).order_by('expiry_date')
        
        if available_batches.exists():
            self.product.expiry_date = available_batches.first().expiry_date
        else:
            self.product.expiry_date = None
        
        # Update product cost_price (weighted average of all batches)
        batches_with_cost = self.product.batches.filter(
            quantity__gt=0,
            cost_price__isnull=False
        )
        
        if batches_with_cost.exists():
            total_quantity = sum(b.quantity for b in batches_with_cost)
            if total_quantity > 0:
                weighted_cost = sum(
                    b.quantity * b.cost_price for b in batches_with_cost
                ) / total_quantity
                self.product.cost_price = weighted_cost
        
        self.product.save()

    @staticmethod
    def deduct_stock_fifo(product, quantity_needed):
        """
        Deduct stock from batches using FIFO method.
        Returns True if successful, False if insufficient stock.
        """
        from django.db import transaction
        
        with transaction.atomic():
            # Get available batches (quantity > 0, not expired, ordered by FIFO)
            available_batches = Batch.objects.filter(
                product=product,
                quantity__gt=0
            ).exclude(
                expiry_date__lt=timezone.now().date()
            ).order_by('manufacturing_date', 'created_at')
            
            # Check if total available stock is sufficient
            total_available = sum(batch.quantity for batch in available_batches)
            if total_available < quantity_needed:
                return False
            
            # Deduct from batches using FIFO
            remaining_to_deduct = quantity_needed
            
            for batch in available_batches:
                if remaining_to_deduct <= 0:
                    break
                
                if batch.quantity >= remaining_to_deduct:
                    # This batch has enough stock
                    batch.quantity -= remaining_to_deduct
                    batch.save()
                    remaining_to_deduct = 0
                else:
                    # Use all stock from this batch and move to next
                    remaining_to_deduct -= batch.quantity
                    batch.quantity = 0
                    batch.save()
            
            # Update product stock_quantity
            product.stock_quantity = sum(
                b.quantity for b in Batch.objects.filter(product=product)
            )
            product.save()
            
            return True

    @staticmethod
    def get_total_stock(product):
        """Get total available stock across all batches"""
        from django.utils import timezone
        return Batch.objects.filter(
            product=product,
            quantity__gt=0
        ).exclude(
            expiry_date__lt=timezone.now().date()
        ).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0


# --------------------
# ORDER MODEL
# --------------------
class Order(models.Model):

    PAYMENT_STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Success", "Success"),
        ("Cancelled", "Cancelled"),
    )

    PAYMENT_METHOD_CHOICES = (
        ("COD", "Cash On Delivery"),
        ("UPI", "UPI"),
        ("Card", "Card"),
        ("NetBanking", "Net Banking"),
    )

    order_id = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    order_date = models.DateTimeField(auto_now_add=True)

    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default="COD"
    )

    transaction_id = models.CharField(max_length=200, blank=True, null=True)

    def save(self, *args, **kwargs):

        if self.payment_method == "COD":
            self.transaction_id = None

        elif not self.transaction_id:
            self.transaction_id = "TXN" + uuid.uuid4().hex[:10].upper()

        super().save(*args, **kwargs)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending"
    )

    total_items = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    DELIVERY_STATUS_CHOICES = (
        ("Order_Placed", "Order Placed"),
        ("Confirmed", "Confirmed"),
        ("Shipped", "Shipped"),
        ("Out_for_Delivery", "Out for Delivery"),
        ("Delivered", "Delivered"),
    )
    delivery_status = models.CharField(
        max_length=30,
        choices=DELIVERY_STATUS_CHOICES,
        default="Order_Placed",
    )

    # 🔥 THIS IS THE MISSING HEART
    def update_totals(self):
        items = self.items.all()
        self.total_items = sum(item.quantity for item in items)
        self.total_amount = sum((item.quantity * item.price) for item in items) or Decimal("0.00")
        self.save(update_fields=["total_items", "total_amount"])

    def __str__(self):
        return self.order_id


# --------------------
# ORDER ITEM MODEL
# --------------------
class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    # Optional link to Product (newer data). Old data can still work via product_name.
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Used for Profit & Loss (can be copied from Product at order time)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def get_total_price(self):
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        # If linked to a Product and cost_price not set, copy cost_price for reporting.
        if self.product and (self.cost_price is None or self.cost_price == 0):
            try:
                self.cost_price = self.product.cost_price
            except Exception:
                pass

        # Keep product_name in sync when product exists (helps old templates)
        if self.product and not self.product_name:
            self.product_name = self.product.name

        super().save(*args, **kwargs)
        self.order.update_totals()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.update_totals()

    def __str__(self):
        return f"{self.product_name} ({self.quantity})"



# --------------------
# TAX + INVOICE MODELS
# --------------------
class Tax(models.Model):
    tax_name = models.CharField(max_length=80)
    tax_percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # e.g. 18.00
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', 'tax_name']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure only one active tax at a time
        if self.is_active:
            Tax.objects.exclude(pk=self.pk).update(is_active=False)

    def __str__(self):
        return f"{self.tax_name} ({self.tax_percentage}%)"

    @staticmethod
    def get_active():
        return Tax.objects.filter(is_active=True).order_by('-updated_at').first()


class Invoice(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ("Paid", "Paid"),
        ("Pending", "Pending"),
        ("Cancelled", "Cancelled"),
    )

    invoice_number = models.CharField(max_length=40, unique=True, blank=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoices")

    issue_date = models.DateTimeField(auto_now_add=True)

    # Tax snapshot
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices")
    tax_name = models.CharField(max_length=80, blank=True, default="")
    tax_percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # Money fields
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending")
    transaction_id = models.CharField(max_length=30, blank=True, null=True)

    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return self.invoice_number or f"Invoice for {self.order.order_id}"

    def _ensure_tax(self):
        """Attach active tax (if invoice.tax is empty) and snapshot values."""
        if self.tax_id is None:
            active = Tax.get_active()
            if active:
                self.tax = active
        if self.tax:
            self.tax_name = self.tax.tax_name
            self.tax_percentage = self.tax.tax_percentage or Decimal("0.00")
        else:
            self.tax_name = ""
            self.tax_percentage = Decimal("0.00")

    def recalculate(self, save: bool = True):
        """Recalculate subtotal/tax/total from invoice items."""
        items = self.items.all()
        subtotal = sum((i.quantity * i.unit_price) for i in items) if items else Decimal("0.00")
        self.subtotal = subtotal or Decimal("0.00")

        self.discount = self.discount or Decimal("0.00")
        if self.discount < 0:
            self.discount = Decimal("0.00")

        self._ensure_tax()
        taxable = max(Decimal("0.00"), self.subtotal - self.discount)
        self.tax_amount = (taxable * (self.tax_percentage / Decimal("100.00"))) if self.tax_percentage else Decimal("0.00")
        self.total_amount = taxable + (self.tax_amount or Decimal("0.00"))

        if save:
            self.save(update_fields=["tax", "tax_name", "tax_percentage", "subtotal", "discount", "tax_amount", "total_amount"])

    @staticmethod
    def _generate_invoice_number():
        # Format: INV-YYYYMMDD-0001
        today = timezone.localdate()
        prefix = f"INV-{today.strftime('%Y%m%d')}-"
        last = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
        if last and last.invoice_number:
            try:
                seq = int(last.invoice_number.split('-')[-1]) + 1
            except Exception:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if not self.invoice_number:
            # best-effort uniqueness in concurrent creates
            with transaction.atomic():
                self.invoice_number = self._generate_invoice_number()

        if not self.customer_id and self.order_id:
            self.customer = self.order.customer

        # Ensure transaction id exists (auto-generated)
        if not self.transaction_id:
            self.transaction_id = "TXN" + uuid.uuid4().hex[:10].upper()

        super().save(*args, **kwargs)

        # On create, if items exist later we'll recalc from view. If items already exist, keep totals correct.
        if creating:
            self._ensure_tax()
            super().save(update_fields=["tax", "tax_name", "tax_percentage"])


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def line_total(self):
        return (self.quantity or 0) * (self.unit_price or 0)
