"""
Prescription Service URL Configuration
"""

from django.urls import path
from .interfaces.http import views

app_name = 'prescription_service'

urlpatterns = [
    # ========================================================================
    # Command Endpoints
    # ========================================================================
    
    # POST /prescriptions/ - Create a new prescription
    path('', views.create_prescription, name='create_prescription'),
    
    # POST /prescriptions/<id>/items/ - Add item to cart
    path('<str:prescription_id>/items/', views.add_cart_item, name='add_cart_item'),
    
    # DELETE /prescriptions/<id>/items/<product_id>/ - Remove item from cart
    path(
        '<str:prescription_id>/items/<str:product_id>/',
        views.remove_cart_item,
        name='remove_cart_item'
    ),
    
    # PUT /prescriptions/<id>/items/<product_id>/quantity/ - Update cart item quantity
    path(
        '<str:prescription_id>/items/<str:product_id>/quantity/',
        views.update_cart_item_quantity,
        name='update_cart_item_quantity'
    ),
    
    # POST /prescriptions/<id>/submit/ - Submit prescription
    path('<str:prescription_id>/submit/', views.submit_prescription, name='submit_prescription'),
    
    # POST /prescriptions/<id>/confirm/ - Confirm prescription
    path('<str:prescription_id>/confirm/', views.confirm_prescription, name='confirm_prescription'),
    
    # POST /prescriptions/<id>/fulfill/ - Fulfill prescription item
    path('<str:prescription_id>/fulfill/', views.fulfill_prescription_item, name='fulfill_prescription_item'),
    
    # POST /prescriptions/<id>/cancel/ - Cancel prescription
    path('<str:prescription_id>/cancel/', views.cancel_prescription, name='cancel_prescription'),
    
    # DELETE /prescriptions/<id>/cart/clear/ - Clear cart
    path('<str:prescription_id>/cart/clear/', views.clear_cart, name='clear_cart'),
    
    # ========================================================================
    # Query Endpoints
    # ========================================================================
    
    # GET /prescriptions/<id>/ - Get prescription by ID
    path('<str:prescription_id>/', views.get_prescription_by_id, name='get_prescription_by_id'),
    
    # GET /prescriptions/customer/<customer_id>/ - Get prescriptions for customer
    path('customer/<str:customer_id>/', views.get_customer_prescriptions, name='get_customer_prescriptions'),
    
    # GET /prescriptions/status/<status>/ - List by status
    path('status/<str:status_filter>/', views.list_prescriptions_by_status, name='list_prescriptions_by_status'),
    
    # GET /prescriptions/draft/ - List draft prescriptions
    path('draft/', views.list_draft_prescriptions, name='list_draft_prescriptions'),
    
    # GET /prescriptions/submitted/ - List submitted prescriptions
    path('submitted/', views.list_submitted_prescriptions, name='list_submitted_prescriptions'),
    
    # GET /prescriptions/active/ - List active prescriptions
    path('active/', views.list_active_prescriptions, name='list_active_prescriptions'),
    
    # GET /prescriptions/recent/ - List recent prescriptions
    path('recent/', views.list_recent_prescriptions, name='list_recent_prescriptions'),
    
    # GET /prescriptions/search/ - Search prescriptions
    path('search/', views.search_prescriptions, name='search_prescriptions'),
    
    # GET /prescriptions/<id>/items/ - Get line items
    path('<str:prescription_id>/items/', views.get_prescription_items, name='get_prescription_items'),
    
    # GET /prescriptions/<id>/validity/ - Check validity
    path('<str:prescription_id>/validity/', views.check_prescription_validity, name='check_prescription_validity'),
]
