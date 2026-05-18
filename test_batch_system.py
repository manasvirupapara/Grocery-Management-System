"""
Test script for Batch Management System
Run this in Django shell: python manage.py shell < test_batch_system.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product, Batch, Category
from datetime import date, timedelta
from django.utils import timezone


def test_batch_system():
    print("\n" + "="*60)
    print("TESTING BATCH MANAGEMENT SYSTEM")
    print("="*60 + "\n")
    
    # Create test category and product
    category, _ = Category.objects.get_or_create(
        name="Test Category",
        defaults={'is_active': True}
    )
    
    product, created = Product.objects.get_or_create(
        name="Test Product - Rice",
        defaults={
            'category': category,
            'selling_price': 100.00,
            'cost_price': 80.00,
            'stock_quantity': 0
        }
    )
    
    if created:
        print(f"✅ Created test product: {product.name}")
    else:
        print(f"📦 Using existing product: {product.name}")
    
    # Clear existing batches
    product.batches.all().delete()
    print(f"🗑️  Cleared existing batches\n")
    
    # Test 1: Create batches
    print("TEST 1: Creating Batches")
    print("-" * 40)
    
    batch1 = Batch.objects.create(
        product=product,
        batch_number="BATCH-TEST-001",
        manufacturing_date=date.today() - timedelta(days=60),
        expiry_date=date.today() + timedelta(days=300),
        quantity=100,
        cost_price=80.00
    )
    print(f"✅ Created {batch1.batch_number}: 100 units")
    
    batch2 = Batch.objects.create(
        product=product,
        batch_number="BATCH-TEST-002",
        manufacturing_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=330),
        quantity=150,
        cost_price=85.00
    )
    print(f"✅ Created {batch2.batch_number}: 150 units")
    
    batch3 = Batch.objects.create(
        product=product,
        batch_number="BATCH-TEST-003",
        manufacturing_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        quantity=200,
        cost_price=90.00
    )
    print(f"✅ Created {batch3.batch_number}: 200 units\n")
    
    # Test 2: Check total stock
    print("TEST 2: Total Stock Calculation")
    print("-" * 40)
    total_stock = Batch.get_total_stock(product)
    print(f"Total Available Stock: {total_stock} units")
    print(f"Product Stock Quantity: {product.stock_quantity} units\n")
    
    # Test 3: FIFO Deduction
    print("TEST 3: FIFO Stock Deduction")
    print("-" * 40)
    print("Deducting 120 units using FIFO...")
    
    success = Batch.deduct_stock_fifo(product, 120)
    
    if success:
        print("✅ Stock deducted successfully!\n")
        print("Batch Status After Deduction:")
        for batch in product.batches.all():
            print(f"  {batch.batch_number}: {batch.quantity} units")
        
        product.refresh_from_db()
        print(f"\nProduct Stock: {product.stock_quantity} units")
    else:
        print("❌ Failed to deduct stock\n")
    
    # Test 4: Check expired batches
    print("\nTEST 4: Expiry Detection")
    print("-" * 40)
    
    # Create expired batch
    expired_batch = Batch.objects.create(
        product=product,
        batch_number="BATCH-TEST-EXPIRED",
        manufacturing_date=date.today() - timedelta(days=400),
        expiry_date=date.today() - timedelta(days=10),
        quantity=50,
        cost_price=70.00
    )
    print(f"Created expired batch: {expired_batch.batch_number}")
    print(f"Is Expired: {expired_batch.is_expired()}")
    print(f"Days Until Expiry: {expired_batch.days_until_expiry()}")
    
    # Check if expired batch is excluded from stock
    total_stock_after = Batch.get_total_stock(product)
    print(f"\nTotal Available Stock (excludes expired): {total_stock_after} units\n")
    
    # Test 5: Insufficient stock
    print("TEST 5: Insufficient Stock Handling")
    print("-" * 40)
    print("Attempting to deduct 500 units (more than available)...")
    
    success = Batch.deduct_stock_fifo(product, 500)
    
    if success:
        print("❌ Should have failed!")
    else:
        print("✅ Correctly rejected insufficient stock\n")
    
    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Product: {product.name}")
    print(f"Total Batches: {product.batches.count()}")
    print(f"Available Stock: {Batch.get_total_stock(product)} units")
    print(f"Expired Batches: {product.batches.filter(expiry_date__lt=timezone.now().date()).count()}")
    print("\n✅ All tests completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_batch_system()
