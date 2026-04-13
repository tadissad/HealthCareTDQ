"""
Pharmacy Service - URL Configuration
Maps HTTP endpoints to views
"""

from django.urls import path
from interfaces.http import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Product creation and commands (POST)
    path('products/create/', views.create_product, name='create_product'),
    path('products/<str:product_id>/receive/', views.receive_inventory, name='receive_inventory'),
    path('products/<str:product_id>/sell/', views.sell_product, name='sell_product'),
    path('products/<str:product_id>/scrap/', views.scrap_product, name='scrap_product'),
    path('products/<str:product_id>/price/', views.change_price, name='change_price'),
    path('products/<str:product_id>/min-stock/', views.adjust_min_stock, name='adjust_min_stock'),
    path('products/<str:product_id>/manufacturer/', views.change_manufacturer, name='change_manufacturer'),
    path('products/check-expiring/', views.check_expiring_products, name='check_expiring_products'),
    path('products/<str:product_id>/deactivate/', views.deactivate_product, name='deactivate_product'),
    
    # Product queries (GET)
    path('products/', views.list_all_products, name='list_all_products'),
    path('products/<str:product_id>/', views.get_product_by_id, name='get_product_by_id'),
    path('products/sku/<str:sku>/', views.get_product_by_sku, name='get_product_by_sku'),
    path('products/atc/<str:atc_code>/', views.get_products_by_atc, name='get_products_by_atc'),
    path('products/active/', views.list_active_products, name='list_active_products'),
    path('products/low-stock/', views.list_low_stock_products, name='list_low_stock_products'),
    path('products/search/', views.search_products, name='search_products'),
    path('products/category/<str:category>/', views.get_products_by_category, name='get_products_by_category'),
    path('products/<str:product_id>/inventory/', views.get_product_inventory, name='get_product_inventory'),
    path('products/expiring/', views.get_expiring_products, name='get_expiring_products'),
]
