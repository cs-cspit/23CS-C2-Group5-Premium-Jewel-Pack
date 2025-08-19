from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Cart

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
