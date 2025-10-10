import os
from pathlib import Path
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db import transaction
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone

from .models import (
    Category, Product, Cart, CartItem,
    Order, OrderItem, OrderStatusHistory, Address, OrderTracking
)
from .forms import SignupForm, LoginForm, CheckoutForm, AddressForm, ProductForm

# -----------------------
# Helpers
# -----------------------
IMAGES_ROOT = settings.BASE_DIR / "core" / "static" / "images"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
RESERVED_FOLDERS = {"css", "js", "__pycache__", ".DS_Store", "icons", "fonts", "svg"}

def _ensure_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart

def _seed_db_from_static_once():
    """
    One-time DB seed helper: if there are no categories/products in DB,
    create Category entries for each folder inside core/static/images and
    create Product entries for each image found.
    This keeps your "zero admin" import minimal.
    """
    if Category.objects.exists() or Product.objects.exists():
        return
    root = IMAGES_ROOT
    if not root.exists():
        return
    for p in sorted(root.iterdir(), key=lambda x: x.name.lower()):
        if p.is_dir() and p.name not in RESERVED_FOLDERS and not p.name.startswith("."):
            cat_slug = slugify(p.name)
            cat, _ = Category.objects.get_or_create(slug=cat_slug, defaults={"name": p.name})
            # collect images recursively
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                    product_name = f.stem.replace("_", " ").replace("-", " ").strip()[:190] or "Item"
                    # avoid duplicate name in same category
                    if Product.objects.filter(name__iexact=product_name, category=cat).exists():
                        continue
                    prod = Product.objects.create(
                        category=cat,
                        name=product_name,
                        price=0.00,
                        stock=10,
                        short_description="Imported from static images folder",
                    )
                    # store a reference to static file path in short_description (optional)
                    prod.short_description += f" | static:{f.relative_to(root).as_posix()}"
                    prod.save()

# -----------------------
# Pages
# -----------------------
def home(request):
    # Fetch data for the new beautiful homepage
    featured_products = Product.objects.filter(is_active=True)[:8]  # Get 8 featured products
    product_count = Product.objects.filter(is_active=True).count()
    category_count = Category.objects.count()
    
    context = {
        'featured_products': featured_products,
        'product_count': product_count,
        'category_count': category_count,
    }
    return render(request, 'home.html', context)

def product_list(request, slug=None):
    # _seed_db_from_static_once()
    qs = Product.objects.filter(is_active=True)
    active_category = None
    if slug:
        active_category = get_object_or_404(Category, slug=slug)
        qs = qs.filter(category=active_category)
    # also allow ?cat=slug param
    catq = request.GET.get("cat")
    if catq and not active_category:
        try:
            active_category = Category.objects.get(slug=catq)
            qs = qs.filter(category=active_category)
        except Category.DoesNotExist:
            pass

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(name__icontains=q)

    sort = request.GET.get("sort", "new")
    if sort == "az":
        qs = qs.order_by("name")
    elif sort == "za":
        qs = qs.order_by("-name")
    elif sort == "price_low":
        qs = qs.order_by("price")
    elif sort == "price_high":
        qs = qs.order_by("-price")
    else:
        qs = qs.order_by("-created_at")

    paginator = Paginator(qs, 12)
    page = request.GET.get("page")
    products = paginator.get_page(page)
    
    context = {
        "products": products, 
        "active_category": active_category, 
        "query": q,
        "sort": sort
    }
    return render(request, "product_list.html", context)

def product_detail(request, slug):
    prod = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=prod.category, is_active=True).exclude(id=prod.id)[:4]
    return render(request, "product_detail.html", {"product": prod, "related": related})

# -----------------------
# Auth
# -----------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    from django.contrib.auth.forms import AuthenticationForm
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if user.is_staff:
                return redirect("core:owner_product_list")
            return redirect("core:home")
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, "login.html", {"form": form})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    form = SignupForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()  # The form's save method handles everything now
            messages.success(request, "Account created successfully! You are now logged in.")
            login(request, user)
            return redirect("core:home")
        else:
            messages.error(request, "Please fix the errors below.")
    return render(request, "signup.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out.")
    return redirect("core:login")

# -----------------------
# Cart (AJAX & non-AJAX)
# -----------------------
def cart_detail(request):
    cart = _ensure_cart(request)
    # Get products list to match IDs with custom names in template
    products = Product.objects.all()[:8]
    return render(request, "cart.html", {"cart": cart, "products": products})

def cart_add(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=400)
    product_id = request.POST.get("product_id")
    quantity = int(request.POST.get("quantity", 1))
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({"success": False, "error": "Product not found"}, status=404)
    cart = _ensure_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()
    return JsonResponse({"success": True, "cart_count": cart.items_count(), "total": str(cart.total())})

def cart_update(request):
    if request.method != "POST":
        return JsonResponse({"success": False}, status=400)
    item_id = request.POST.get("item_id")
    qty = int(request.POST.get("quantity", 1))
    try:
        item = CartItem.objects.get(id=item_id)
    except CartItem.DoesNotExist:
        return JsonResponse({"success": False}, status=404)
    if qty <= 0:
        cart = item.cart
        item.delete()
        return JsonResponse({"success": True, "total": str(cart.total()), "cart_count": cart.items_count()})
    item.quantity = qty
    item.save()
    return JsonResponse({"success": True, "sub": str(item.subtotal()), "total": str(item.cart.total()), "cart_count": item.cart.items_count()})

def cart_remove(request):
    if request.method != "POST":
        return JsonResponse({"success": False}, status=400)
    item_id = request.POST.get("item_id")
    try:
        item = CartItem.objects.get(id=item_id)
    except CartItem.DoesNotExist:
        return JsonResponse({"success": False}, status=404)
    cart = item.cart
    item.delete()
    return JsonResponse({"success": True, "total": str(cart.total()), "cart_count": cart.items_count()})

# -----------------------
# Checkout / Orders
# -----------------------
@login_required
@transaction.atomic
def checkout(request):
    cart = _ensure_cart(request)
    if cart.items.count() == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect("core:cart_detail")
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total = cart.total()
            order.save()
            for item in cart.items.all():
                OrderItem.objects.create(order=order, product=item.product, price=item.product.get_price(), quantity=item.quantity)
                # reduce stock if available
                if item.product.stock >= item.quantity:
                    item.product.stock -= item.quantity
                    item.product.save()
            cart.items.all().delete()
            messages.success(request, "Order placed. Thank you!")
            return redirect("core:order_success", order_id=order.id)
        else:
            messages.error(request, "Please correct errors below.")
    else:
        initial = {"full_name": request.user.get_full_name() or request.user.username, "email": request.user.email}
        form = CheckoutForm(initial=initial)
    return render(request, "checkout.html", {"cart": cart, "form": form})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user != request.user and not request.user.is_staff:
        return redirect("core:home")
    return render(request, "order_success.html", {"order": order})

@login_required
def my_orders(request):
    # Default to orders from last 1 month
    one_month_ago = timezone.now() - timedelta(days=30)
    
    # Get date filter from request (if provided)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    orders = Order.objects.filter(user=request.user)
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__gte=start, created_at__date__lte=end)
        except ValueError:
            # Invalid date format, use default
            orders = orders.filter(created_at__gte=one_month_ago)
    else:
        # Default: last 1 month
        orders = orders.filter(created_at__gte=one_month_ago)
    
    orders = orders.order_by("-created_at")
    
    context = {
        'orders': orders,
        'start_date': start_date or one_month_ago.strftime('%Y-%m-%d'),
        'end_date': end_date or timezone.now().strftime('%Y-%m-%d'),
    }
    return render(request, "orders.html", context)

@login_required
def my_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # Get tracking information
    tracking = OrderTracking.objects.filter(order=order).first()
    # Get status history
    history = OrderStatusHistory.objects.filter(order=order).order_by('-created_at')
    
    context = {
        'order': order,
        'tracking': tracking,
        'history': history,
    }
    return render(request, "order_detail.html", context)

# -----------------------
# Owner pages
# -----------------------
def _owner_check(user):
    return user.is_staff

@user_passes_test(_owner_check)
def owner_orders(request):
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    orders = Order.objects.all()
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__gte=start, created_at__date__lte=end)
        except ValueError:
            pass
    
    orders = orders.order_by("-created_at")
    
    # Status choices for filter dropdown
    status_choices = [
        ('', 'All Orders'),
        ('PLACED', 'Order Placed'),
        ('IN_PROCESS', 'Order in Process'),
        ('DELIVERY_SOON', 'Delivery Soon'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    context = {
        'orders': orders,
        'status_choices': status_choices,
        'current_status': status_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, "owner_orders.html", context)

@user_passes_test(_owner_check)
def owner_update_order_status(request, order_id):
    if request.method != "POST":
        return HttpResponseForbidden("Invalid method")
    new_status = request.POST.get("status")
    note = request.POST.get("note", "")
    order = get_object_or_404(Order, id=order_id)
    
    # Valid status choices
    valid_statuses = ['PLACED', 'IN_PROCESS', 'DELIVERY_SOON', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED']
    
    if new_status not in valid_statuses:
        messages.error(request, "Invalid status")
        return redirect("core:owner_orders")
    
    old_status = order.status
    order.status = new_status
    order.save()
    
    # Create manual history entry with note if provided
    if note:
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            note=note,
            updated_by=request.user
        )
    
    messages.success(request, f"Order #{order.id} status updated to {order.get_status_display()}")
    return redirect("core:owner_orders")
    old_status = order.status
    order.status = new_status
    order.save()
    OrderStatusHistory.objects.create(order=order, old_status=old_status, new_status=new_status, note=note)
    messages.success(request, f"Order #{order.id} status updated to {order.get_status_display()}.")
    return redirect("core:owner_orders")

@user_passes_test(_owner_check)
def owner_product_list(request):
    products = Product.objects.all().order_by("-created_at")
    return render(request, "owner_product_list.html", {"products": products})

@user_passes_test(_owner_check)
def owner_product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product created successfully.")
            return redirect("core:owner_product_list")
    else:
        form = ProductForm()
    return render(request, "owner_product_form.html", {"form": form})

@user_passes_test(_owner_check)
def owner_product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect("core:owner_product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "owner_product_form.html", {"form": form})

@user_passes_test(_owner_check)
def owner_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect("core:owner_product_list")
    return render(request, "owner_product_delete.html", {"product": product})

# -----------------------
# Info
# -----------------------
def about(request):
    return render(request, "about.html")

def contact(request):
    return render(request, "contact.html")
