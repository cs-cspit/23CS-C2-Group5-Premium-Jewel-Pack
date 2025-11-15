from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Cart, Order, OrderTracking, OrderStatusHistory

@receiver(user_logged_in)
def merge_carts(sender, user, request, **kwargs):
    # merge session cart into user cart upon login
    if not request.session.session_key:
        return
    session_key = request.session.session_key
    guest_cart = Cart.objects.filter(session_key=session_key).order_by("-created_at").first()
    if not guest_cart:
        return
    user_cart, _ = Cart.objects.get_or_create(user=user)
    for item in guest_cart.items.all():
        existing = user_cart.items.filter(product=item.product).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
        else:
            item.cart = user_cart
            item.save()
    guest_cart.delete()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # placeholder for creating related profile if you extend later
    if created:
        # no profile model now; if you add, create here
        pass


# Order tracking signals
@receiver(post_save, sender=Order)
def create_order_tracking(sender, instance, created, **kwargs):
    """Create OrderTracking when Order is created"""
    if created:
        # Build full address from Order model fields
        address_parts = [instance.address_line1]
        if instance.address_line2:
            address_parts.append(instance.address_line2)
        address_parts.extend([instance.city, instance.state, instance.postal_code])
        full_address = ", ".join(address_parts)
        
        tracking = OrderTracking.objects.create(
            order=instance,
            placed_at=timezone.now(),
            delivery_address=full_address
        )


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """Track order status changes and update timestamps"""
    if instance.pk:  # Only for existing orders (updates)
        try:
            old_order = Order.objects.get(pk=instance.pk)
            if old_order.status != instance.status:
                # Status has changed, create history record
                OrderStatusHistory.objects.create(
                    order=instance,
                    old_status=old_order.status,
                    new_status=instance.status,
                    note=f"Status changed from {old_order.get_status_display()} to {instance.get_status_display()}"
                )
                
                # Update tracking timestamps
                tracking, created = OrderTracking.objects.get_or_create(order=instance)
                now = timezone.now()
                
                if instance.status == 'PLACED':
                    tracking.placed_at = now
                elif instance.status == 'IN_PROCESS':
                    tracking.in_process_at = now
                elif instance.status == 'DELIVERY_SOON':
                    tracking.delivery_soon_at = now
                elif instance.status == 'OUT_FOR_DELIVERY':
                    tracking.out_for_delivery_at = now
                elif instance.status == 'DELIVERED':
                    tracking.delivered_at = now
                elif instance.status == 'CANCELLED':
                    tracking.cancelled_at = now
                
                tracking.save()
        
        except Order.DoesNotExist:
            pass
