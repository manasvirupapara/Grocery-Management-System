"""
URL Configuration for Product Variant System
"""

from django.urls import path
from . import views_variant

urlpatterns = [
    # Product pages
    path('products/', views_variant.product_list, name='product_list'),
    path('product/<int:product_id>/', views_variant.product_detail, name='product_detail'),
    path('category/<int:category_id>/products/', views_variant.category_products, name='category_products'),
    path('search/', views_variant.search_products, name='search_products'),
    
    # API endpoints
    path('api/variant/<int:variant_id>/', views_variant.get_variant_details, name='get_variant_details'),
    path('api/cart/add-variant/', views_variant.add_variant_to_cart, name='add_variant_to_cart'),
]
