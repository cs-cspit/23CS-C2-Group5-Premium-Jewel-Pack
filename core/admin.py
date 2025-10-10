# core/admin.py

from django.contrib import admin
from .models import (
    Category, Product, Address, Cart, CartItem,
    Order, OrderItem, OrderStatusHistory, UserProfile, OrderTracking
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


class TrackingInline(admin.StackedInline):
    model = OrderTracking
    readonly_fields = ("placed_at", "in_process_at", "delivery_soon_at", "out_for_delivery_at", "delivered_at", "cancelled_at", "last_updated")
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "total", "status", "created_at")
    list_filter = ("status", "created_at")
    inlines = [OrderItemInline, TrackingInline, StatusInline]
    actions = ["mark_in_process", "mark_delivery_soon", "mark_out_for_delivery", "mark_delivered"]

    def mark_in_process(self, request, queryset):
        for order in queryset:
            old = order.status
            order.status = "IN_PROCESS"
            order.save()
    mark_in_process.short_description = "Mark selected orders as In Process"
    
    def mark_delivery_soon(self, request, queryset):
        for order in queryset:
            old = order.status
            order.status = "DELIVERY_SOON"
            order.save()
    mark_delivery_soon.short_description = "Mark selected orders as Delivery Soon"
    
    def mark_out_for_delivery(self, request, queryset):
        for order in queryset:
            old = order.status
            order.status = "OUT_FOR_DELIVERY"
            order.save()
    mark_out_for_delivery.short_description = "Mark selected orders as Out for Delivery"
    
    def mark_delivered(self, request, queryset):
        for order in queryset:
            old = order.status
            order.status = "DELIVERED"
            order.save()
    mark_delivered.short_description = "Mark selected orders as Delivered"


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ("order", "get_order_status", "placed_at", "delivered_at", "get_progress")
    list_filter = ("order__status", "placed_at", "delivered_at")
    search_fields = ("order__id", "order__full_name", "tracking_number")
    readonly_fields = ("placed_at", "in_process_at", "delivery_soon_at", "out_for_delivery_at", "delivered_at", "cancelled_at", "last_updated")
    
    def get_order_status(self, obj):
        return obj.order.get_status_display()
    get_order_status.short_description = "Status"
    
    def get_progress(self, obj):
        return f"{obj.get_progress_percentage()}%"
    get_progress.short_description = "Progress"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "firm_name", "mobile_number", "created_at")
    search_fields = ("user__username", "user__first_name", "user__email", "firm_name", "mobile_number")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")
