# core/admin.py

from django.contrib import admin
from .models import (
    Category, Product, Address, Cart, CartItem,
    Order, OrderItem, OrderStatusHistory
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "created_at")
    list_filter = ("category", "is_active")
    search_fields = ("name", "sku", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "city", "state", "postal_code", "is_default")  # ✅ fixed
    search_fields = ("user__username", "full_name", "postal_code")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "created_at")
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ("product", "price", "quantity")
    extra = 0


class StatusInline(admin.TabularInline):
    model = OrderStatusHistory
    readonly_fields = ("old_status", "new_status", "note", "created_at")
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "total", "status", "created_at")
    list_filter = ("status", "created_at")
    inlines = [OrderItemInline, StatusInline]
    actions = ["mark_shipped"]

    def mark_shipped(self, request, queryset):
        for order in queryset:
            old = order.status
            order.status = "SHIPPED"
            order.save()
            OrderStatusHistory.objects.create(
                order=order,
                old_status=old,
                new_status="SHIPPED",
                note="Marked shipped from admin action"
            )
    mark_shipped.short_description = "Mark selected orders as shipped"
