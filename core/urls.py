from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Auth
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    # Products / catalog
    path("products/", views.product_list, name="product_list"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("category/<slug:slug>/", views.product_list, name="product_list_by_category"),

    # Cart
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/", views.cart_remove, name="cart_remove"),

    # Checkout & Orders
    path("checkout/", views.checkout, name="checkout"),
    path("order/success/<int:order_id>/", views.order_success, name="order_success"),

    # User orders
    path("my-orders/", views.my_orders, name="my_orders"),
    path("my-orders/<int:order_id>/", views.my_order_detail, name="my_order_detail"),

    # Owner management (requires is_staff check inside view)
    path("owner/orders/", views.owner_orders, name="owner_orders"),
    path("owner/order/<int:order_id>/status/", views.owner_update_order_status, name="owner_update_order_status"),

    # Info
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]
