"""
Dispensing Service - URL Configuration
"""

from django.urls import path
from interfaces.http import views

urlpatterns = [
    # Health
    path('health/', views.health_check, name='health_check'),
    
    # Order Commands (POST)
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<str:order_id>/confirm/', views.confirm_order, name='confirm_order'),
    path('orders/<str:order_id>/dispense/', views.dispense_order_item, name='dispense_order_item'),
    path('orders/<str:order_id>/payment/', views.process_payment, name='process_payment'),
    path('orders/<str:order_id>/payment-failure/', views.handle_payment_failure, name='handle_payment_failure'),
    path('orders/<str:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<str:order_id>/hold/', views.put_order_on_hold, name='put_order_on_hold'),
    path('orders/<str:order_id>/resume/', views.resume_order, name='resume_order'),
    path('orders/<str:order_id>/shipping/', views.update_shipping_address, name='update_shipping_address'),
    path('orders/<str:order_id>/remove-item/', views.remove_line_item, name='remove_line_item'),
    path('orders/<str:order_id>/discount/', views.apply_discount, name='apply_discount'),
    path('orders/<str:order_id>/validate-prescription/', views.validate_prescription, name='validate_prescription'),
    
    # Order Queries (GET)
    path('orders/', views.list_all_orders, name='list_all_orders'),
    path('orders/<str:order_id>/', views.get_order_by_id, name='get_order_by_id'),
    path('orders/<str:order_id>/inventory/', views.get_order_inventory, name='get_order_inventory'),
    path('orders/pending/', views.list_pending_orders, name='list_pending_orders'),
    path('orders/ready-for-dispensing/', views.list_ready_for_dispensing, name='list_ready_for_dispensing'),
    path('orders/dispensing/', views.list_dispensing_orders, name='list_dispensing_orders'),
    path('orders/status/<str:status>/', views.list_orders_by_status, name='list_orders_by_status'),
    path('orders/with-prescription/', views.list_prescription_orders, name='list_prescription_orders'),
    path('orders/recent/', views.get_recent_orders, name='get_recent_orders'),
    path('customers/<str:customer_id>/orders/', views.get_customer_orders, name='get_customer_orders'),
]
