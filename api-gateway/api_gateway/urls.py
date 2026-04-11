from django.urls import path
from app.views import (
    IndexView, LoginView, RegisterView, LogoutView,
    ProductDetailView, ReviewSubmitView,
    CartView, CartAddView, CartRemoveView,
    CheckoutView, OrderHistoryView, OrderDetailView,
    AIChatView, AIRecommendView,
    ProfileView, ProfileSettingsView,
    HealthView,
)

urlpatterns = [
    # ── Auth ────────────────────────────────────────────
    path('',          IndexView.as_view(),    name='index'),
    path('login/',    LoginView.as_view(),    name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/',   LogoutView.as_view(),   name='logout'),

    # ── Products ─────────────────────────────────────────
    path('products/<int:product_id>/',        ProductDetailView.as_view(),  name='product-detail'),
    path('products/<int:product_id>/review/', ReviewSubmitView.as_view(),   name='review-submit'),

    # ── Cart ──────────────────────────────────────────────
    path('cart/',                      CartView.as_view(),       name='cart'),
    path('cart/add/',                  CartAddView.as_view(),    name='cart-add'),
    path('cart/remove/<int:item_id>/', CartRemoveView.as_view(), name='cart-remove'),
    path('checkout/',                  CheckoutView.as_view(),   name='checkout'),

    # ── Orders ────────────────────────────────────────────
    path('orders/',                 OrderHistoryView.as_view(), name='orders'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(),   name='order-detail'),

    # ── AI Features ──────────────────────────────────────
    path('ai/chat/',      AIChatView.as_view(),      name='ai-chat'),
    path('ai/recommend/', AIRecommendView.as_view(),  name='ai-recommend'),

    # ── Profile ───────────────────────────────────────────
    path('profile/',          ProfileView.as_view(),         name='profile'),
    path('profile/settings/', ProfileSettingsView.as_view(), name='profile-settings'),

    # ── System Health ─────────────────────────────────────
    path('health/', HealthView.as_view(), name='health'),
]
