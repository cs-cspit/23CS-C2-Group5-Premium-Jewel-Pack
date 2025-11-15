# core/models.py

"""
Models for PJP e-commerce app.

- Category / Product (standard)
- Cart / CartItem (session or user)
- Order / OrderItem / OrderStatusHistory for admin tracking
- Address for user shipping addresses
"""
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

# -------------------------
# Catalog
# -------------------------
class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to="categories/", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    sku = models.CharField(max_length=64, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/%Y/%m/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_price(self):
        if self.discount_price:
            return max(self.price - self.discount_price, Decimal("0.00"))
        return self.price

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.name}-{self.category_id or ''}"
            self.slug = slugify(base)[:220]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:product_detail", args=[self.slug])

    def __str__(self):
        return self.name


# -------------------------
# Addresses
# -------------------------
class Address(models.Model):
    user = models.ForeignKey(User, related_name="addresses", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    address_line1 = models.CharField(max_length=250)
    address_line2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)  # ✅ correct field
    country = models.CharField(max_length=50, default="India")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} — {self.city}"


# -------------------------
# Cart
# -------------------------
class Cart(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.user.username if self.user else self.session_key
        return f"Cart({self.pk}) for {who}"

    def items_count(self):
        return sum(item.quantity for item in self.items.all())

    def total(self):
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.subtotal()
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

    def subtotal(self):
        return self.product.get_price() * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


# -------------------------
# Orders & status history
# -------------------------
ORDER_STATUS = [
    ("PLACED", "Order Placed"),
    ("IN_PROCESS", "Order in Process"),
    ("DELIVERY_SOON", "Delivery Soon"),
    ("OUT_FOR_DELIVERY", "Out for Delivery"),
    ("DELIVERED", "Delivered"),
    ("CANCELLED", "Cancelled"),
]

class Order(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address_line1 = models.CharField(max_length=250)
    address_line2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50, default="India")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="PLACED")
    payment_method = models.CharField(max_length=50, default="COD")
    tracking_code = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def recalc_total(self):
        total = Decimal("0.00")
        for it in self.items.all():
            total += it.price * it.quantity
        self.total = total
        self.save()
        return self.total

    def __str__(self):
        return f"Order {self.pk} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, related_name="history", on_delete=models.CASCADE)
    old_status = models.CharField(max_length=20, choices=ORDER_STATUS)
    new_status = models.CharField(max_length=20, choices=ORDER_STATUS)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Order #{self.order_id}: {self.old_status} → {self.new_status}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"


class OrderTracking(models.Model):
    """Detailed order tracking information"""
    order = models.OneToOneField(Order, related_name="tracking", on_delete=models.CASCADE)
    
    # Tracking timestamps for each stage
    placed_at = models.DateTimeField(null=True, blank=True)
    in_process_at = models.DateTimeField(null=True, blank=True)
    delivery_soon_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Additional tracking details
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    courier_service = models.CharField(max_length=100, blank=True)
    delivery_address = models.TextField(blank=True)
    
    # Current status details
    current_location = models.CharField(max_length=200, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Tracking for Order #{self.order.id}"
    
    def get_current_stage_timestamp(self):
        """Get timestamp for current order status"""
        status_mapping = {
            'PLACED': self.placed_at,
            'IN_PROCESS': self.in_process_at,
            'DELIVERY_SOON': self.delivery_soon_at,
            'OUT_FOR_DELIVERY': self.out_for_delivery_at,
            'DELIVERED': self.delivered_at,
            'CANCELLED': self.cancelled_at,
        }
        return status_mapping.get(self.order.status)
    
    def get_progress_percentage(self):
        """Calculate order progress percentage"""
        status_progress = {
            'PLACED': 20,
            'IN_PROCESS': 40,
            'DELIVERY_SOON': 60,
            'OUT_FOR_DELIVERY': 80,
            'DELIVERED': 100,
            'CANCELLED': 0,
        }
        return status_progress.get(self.order.status, 0)
    
    def get_completed_stages(self):
        """Get list of completed stages with timestamps"""
        stages = []
        if self.placed_at:
            stages.append(('PLACED', 'Order Placed', self.placed_at))
        if self.in_process_at:
            stages.append(('IN_PROCESS', 'Order in Process', self.in_process_at))
        if self.delivery_soon_at:
            stages.append(('DELIVERY_SOON', 'Delivery Soon', self.delivery_soon_at))
        if self.out_for_delivery_at:
            stages.append(('OUT_FOR_DELIVERY', 'Out for Delivery', self.out_for_delivery_at))
        if self.delivered_at:
            stages.append(('DELIVERED', 'Delivered', self.delivered_at))
        if self.cancelled_at:
            stages.append(('CANCELLED', 'Cancelled', self.cancelled_at))
        return stages

    class Meta:
        verbose_name = "Order Tracking"
        verbose_name_plural = "Order Tracking"


# -------------------------
# User Profile for Additional Information
# -------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    firm_name = models.CharField(max_length=100, blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
