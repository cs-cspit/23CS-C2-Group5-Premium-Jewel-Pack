#!/usr/bin/env python
import os
import sys
import django

# Add project root to path
sys.path.insert(0, r'E:\Python Django\pjp_new')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pjp.settings')

django.setup()

from core.models import Category, Product

print("=== Database Status ===")
print(f"Categories: {Category.objects.count()}")
print(f"Products: {Product.objects.count()}")

print("\n=== Categories ===")
for category in Category.objects.all():
    product_count = category.products.count()
    print(f"- {category.name} (slug: {category.slug}) - {product_count} products")

print("\n=== Recent Products ===")
for product in Product.objects.all()[:10]:
    print(f"- {product.name} (Category: {product.category.name}) - ₹{product.price}")