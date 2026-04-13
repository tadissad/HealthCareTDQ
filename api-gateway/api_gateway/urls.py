from django.urls import path
from app.views import (
    IndexView, LoginView, RegisterView, LogoutView,
    ProductDetailView, ReviewSubmitView,
    CartView, CartAddView, CartRemoveView, CartPatchView,
    CheckoutView, OrderHistoryView, OrderDetailView,
    AIChatView, AIRecommendView,
    ProfileView, ProfileSettingsView,
    HealthView,
    AdminDashboardView, AdminProductListView, AdminProductCreateView,
    AdminProductEditView, AdminProductDeleteView,
    AdminOrderListView, AdminOrderUpdateView,
    AdminUserListView,
    StaffProductListView, StaffProductCreateView,
    StaffProductEditView, StaffProductDeleteView,
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
    path('cart/patch/<int:item_id>/',  CartPatchView.as_view(),  name='cart-patch'),
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

    # ── Admin Portal ──────────────────────────────────────
    path('admin/dashboard/',                            AdminDashboardView.as_view(),    name='admin-dashboard'),
    path('admin/products/',                             AdminProductListView.as_view(),  name='admin-products'),
    path('admin/products/create/',                      AdminProductCreateView.as_view(), name='admin-product-create'),
    path('admin/products/<int:product_id>/edit/',       AdminProductEditView.as_view(),  name='admin-product-edit'),
    path('admin/products/<int:product_id>/delete/',     AdminProductDeleteView.as_view(), name='admin-product-delete'),
    path('admin/orders/',                               AdminOrderListView.as_view(),    name='admin-orders'),
    path('admin/orders/<int:order_id>/update/',         AdminOrderUpdateView.as_view(),  name='admin-order-update'),
    path('admin/users/',                                AdminUserListView.as_view(),     name='admin-users'),

    # ── Staff Portal (chỉ sản phẩm) ───────────────────────
    path('staff/products/',                             StaffProductListView.as_view(),   name='staff-products'),
    path('staff/products/create/',                      StaffProductCreateView.as_view(), name='staff-product-create'),
    path('staff/products/<int:product_id>/edit/',       StaffProductEditView.as_view(),   name='staff-product-edit'),
    path('staff/products/<int:product_id>/delete/',     StaffProductDeleteView.as_view(), name='staff-product-delete'),

    # ── System Health ─────────────────────────────────────
    path('health/', HealthView.as_view(), name='health'),
]
