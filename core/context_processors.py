"""
context processor to expose:
- GLOBAL_CATEGORIES : scanned from core/static/images subfolders (fast)
- GLOBAL_SLIDER_IMAGES : list of slider images (if core/static/images/slider exists)
- CART_COUNT : number of items in active cart (session or user)
"""
import os
from pathlib import Path
from django.conf import settings
from django.utils.text import slugify
from .models import Cart

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
RESERVED = {"css", "js", "__pycache__", ".DS_Store", "icons", "fonts", "svg"}

ROOT = settings.BASE_DIR / "core" / "static" / "images"

def _list_categories():
    out = []
    if ROOT.exists():
        for p in sorted(ROOT.iterdir(), key=lambda x: x.name.lower()):
            if p.is_dir() and p.name not in RESERVED and not p.name.startswith("."):
                # count images inside
                cnt = 0
                for _ in p.glob("**/*"):
                    pass
                # count only files with image ext
                for f in p.rglob("*"):
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                        cnt += 1
                out.append({"name": p.name, "slug": slugify(p.name), "count": cnt})
    return out

def _slider_images():
    sdir = ROOT / "slider"
    out = []
    if sdir.exists():
        for f in sorted(sdir.iterdir()):
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                out.append(f"images/slider/{f.name}")
    return out

def common(request):
    # cart count
    cart_count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).order_by("-created_at").first()
            if cart:
                cart_count = cart.items_count()
        else:
            key = request.session.session_key
            if not key:
                request.session.create()
                key = request.session.session_key
            cart = Cart.objects.filter(session_key=key).order_by("-created_at").first()
            if cart:
                cart_count = cart.items_count()
    except Exception:
        cart_count = 0

    return {
        "GLOBAL_CATEGORIES": _list_categories(),
        "GLOBAL_SLIDER_IMAGES": _slider_images(),
        "CART_COUNT": cart_count,
    }
