"""
Dispensing Service Infrastructure Layer - ORM Models
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
import json


class OrderModel(models.Model):
    """
    ORM Model for Order persistence
    Maps domain Order aggregate to database
    """
    order_id = models.CharField(max_length=36, unique=True, primary_key=True)
    customer_id = models.CharField(max_length=36, db_index=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'),
            ('DISPENSING', 'Dispensing'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
            ('ON_HOLD', 'On Hold'),
        ],
        default='PENDING',
        db_index=True
    )
    
    # Amounts
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='VND')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payment
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('CASH', 'Cash'),
            ('CARD', 'Card'),
            ('INSURANCE', 'Insurance'),
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('E_WALLET', 'E-Wallet'),
        ],
        default='CASH'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('AUTHORIZED', 'Authorized'),
            ('PAID', 'Paid'),
            ('FAILED', 'Failed'),
            ('REFUNDED', 'Refunded'),
        ],
        default='PENDING'
    )
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Shipping
    shipping_street = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_district = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, default='Vietnam')
    shipping_notes = models.TextField(blank=True)
    
    # Prescription
    has_prescription = models.BooleanField(default=False)
    prescription_id = models.CharField(max_length=100, blank=True, null=True)
    prescriber_name = models.CharField(max_length=255, blank=True)
    prescription_date = models.DateField(blank=True, null=True)
    prescription_valid_until = models.DateField(blank=True, null=True)
    
    # Dates
    order_date = models.DateTimeField(auto_now_add=True)
    confirmed_date = models.DateTimeField(blank=True, null=True)
    dispensed_date = models.DateTimeField(blank=True, null=True)
    
    # Additional
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dispensing_orders'
        indexes = [
            models.Index(fields=['customer_id']),
            models.Index(fields=['status']),
            models.Index(fields=['order_date']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"Order {self.order_id} - {self.status}"


class OrderItemModel(models.Model):
    """
    ORM Model for OrderItem (line item in order)
    """
    order_item_id = models.CharField(max_length=36, unique=True, primary_key=True)
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name='order_items')
    
    # Product reference
    product_id = models.CharField(max_length=36)
    sku = models.CharField(max_length=50)
    product_name = models.CharField(max_length=255)
    
    # Quantities
    quantity_ordered = models.BigIntegerField()
    quantity_dispensed = models.BigIntegerField(default=0)
    quantity_unit = models.CharField(max_length=50, default='box')
    
    # Pricing
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='VND')
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dispensing_order_items'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['sku']),
        ]
    
    def __str__(self):
        return f"{self.sku} x {self.quantity_ordered} - Order {self.order_id}"


class DomainEventModel(models.Model):
    """
    ORM Model for Domain Event persistence
    Tracks all domain events raised by orders
    """
    event_id = models.CharField(max_length=36, unique=True, primary_key=True)
    order_id = models.CharField(max_length=36, db_index=True)
    customer_id = models.CharField(max_length=36, db_index=True)
    
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField()
    
    occurred_at = models.DateTimeField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dispensing_domain_events'
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['processed']),
            models.Index(fields=['occurred_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} on Order {self.order_id}"
