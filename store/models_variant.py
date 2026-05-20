"""
Product Variant Models for Grocery Management System
Allows products to have multiple weight/size options with individual pricing
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Product(models.Model):
    """
    Main Product Model - Base product information
    """
    category = models.ForeignKey(
        'Category', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="products"
    )
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Product metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
    
    def __str__(self):
        return self.name
    
    def get_default_variant(self):
        """Get the first active variant or None"""
        return self.variants.filter(is_active=True).first()
    
    def get_price_range(self):
        """Get min and max price across all variants"""
        variants = self.variants.filter(is_active=True)
        if not variants.exists():
            return None, None
        
        prices = variants.values_list('price', flat=True)
        return min(prices), max(prices)
    
    def total_stock(self):
        """Get total stock across all variants"""
        return self.variants.aggregate(
            total=models.Sum('stock')
        )['total'] or 0
    
    def has_stock(self):
        """Check if any variant has stock"""
        return self.variants.filter(stock__gt=0).exists()


class ProductVariant(models.Model):
    """
    Product Variant Model - Different weight/size options for a product
    """
    
    STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='variants'
    )
    
    # Variant details
    weight = models.CharField(
        max_length=50,
        help_text="e.g., 100g, 250g, 500g, 1kg, 5kg"
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost price for profit calculation"
    )
    
    # Stock management
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    low_stock_alert = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Alert when stock falls below this number"
    )
    
    # Status (auto-calculated)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_stock',
        editable=False
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['product', 'weight']
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        unique_together = ['product', 'weight']
    
    def __str__(self):
        return f"{self.product.name} - {self.weight}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-calculate status"""
        self.status = self.calculate_status()
        super().save(*args, **kwargs)
    
    def calculate_status(self):
        """Calculate stock status based on current stock"""
        if self.stock == 0:
            return 'out_of_stock'
        elif self.stock <= self.low_stock_alert:
            return 'low_stock'
        else:
            return 'in_stock'
    
    def is_in_stock(self):
        """Check if variant is in stock"""
        return self.stock > 0
    
    def is_low_stock(self):
        """Check if variant is low on stock"""
        return 0 < self.stock <= self.low_stock_alert
    
    def is_out_of_stock(self):
        """Check if variant is out of stock"""
        return self.stock == 0
    
    def get_status_display_color(self):
        """Get color for status display"""
        colors = {
            'in_stock': '#28a745',
            'low_stock': '#ffc107',
            'out_of_stock': '#dc3545',
        }
        return colors.get(self.status, '#6c757d')
    
    def decrease_stock(self, quantity):
        """Decrease stock by quantity"""
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity):
        """Increase stock by quantity"""
        self.stock += quantity
        self.save()
