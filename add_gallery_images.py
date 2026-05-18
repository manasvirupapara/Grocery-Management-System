import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product, ProductImage

# Add gallery images for Basmati Rice
try:
    basmati_rice = Product.objects.get(name__icontains='Basmati Rice')
    
    # Check if gallery images already exist
    existing_count = ProductImage.objects.filter(product=basmati_rice).count()
    
    print(f"Current gallery images for {basmati_rice.name}: {existing_count}")
    
    # Add more gallery images if less than 2
    if existing_count < 2:
        gallery_images = [
            'products/gallery/basmati_rice_2.png',
            'products/gallery/rice_2.png',
        ]
        
        for img_path in gallery_images:
            ProductImage.objects.create(
                product=basmati_rice,
                image=img_path,
                is_primary=False
            )
            print(f"Added gallery image: {img_path}")
        
        print(f"\nSuccessfully added {len(gallery_images)} gallery images for {basmati_rice.name}")
    else:
        print(f"Already has enough gallery images")
        
except Product.DoesNotExist:
    print("Basmati Rice product not found!")
except Exception as e:
    print(f"Error: {e}")

# Add gallery images for regular Rice
try:
    rice = Product.objects.get(name='Rice')
    
    # Check if gallery images already exist
    existing_count = ProductImage.objects.filter(product=rice).count()
    
    if existing_count > 0:
        print(f"\nGallery images already exist for {rice.name}: {existing_count} images")
    else:
        # Add gallery images
        gallery_images = [
            'products/gallery/rice_2.png',
            'products/gallery/rice_2_aRRgxLG.png',
        ]
        
        for img_path in gallery_images:
            ProductImage.objects.create(
                product=rice,
                image=img_path,
                is_primary=False
            )
            print(f"Added gallery image: {img_path}")
        
        print(f"\nSuccessfully added {len(gallery_images)} gallery images for {rice.name}")
        
except Product.DoesNotExist:
    print("\nRice product not found!")
except Exception as e:
    print(f"Error: {e}")

print("\n✓ Gallery images setup complete!")
