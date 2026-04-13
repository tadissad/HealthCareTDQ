"""
Pharmacy Infrastructure Layer - ORM Models
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
import json


class ProductModel(models.Model):
    """
    ORM Model for Product persistence
    All complex domain logic is in domain layer; this is data mapping only
    """
    # Identity
    product_id = models.CharField(max_length=36, unique=True, primary_key=True)
    
    # Basic Information
    sku = models.CharField(max_length=50, unique=True)
    generic_name = models.CharField(max_length=255)
    trade_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Medical Classification
    dosage_form = models.CharField(max_length=50)  # tablet, capsule, liquid, etc.
    dosage_strength = models.CharField(max_length=100)  # 500mg, 10%v/v, etc.
    atc_code = models.CharField(max_length=10)  # Anatomical Therapeutic Chemical
    icd_codes = models.JSONField(default=list)  # ICD-10 codes (JSON list)
    
    # Manufacturer Information
    manufacturer_name = models.CharField(max_length=255)
    manufacturer_country = models.CharField(max_length=100)
    
    # Regulatory & Pricing
    requires_prescription = models.BooleanField(default=False)
    price_amount = models.DecimalField(max_digits=12, decimal_places=2)
    price_currency = models.CharField(max_length=3, default='VND')
    
    # Inventory Management
    total_quantity_value = models.BigIntegerField(default=0)
    total_quantity_unit = models.CharField(max_length=50, default='box')
    min_stock_level_value = models.BigIntegerField(default=10)
    reorder_point_value = models.BigIntegerField(default=20)
    
    # Status
    active = models.BooleanField(default=True)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pharmacy_products'
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['atc_code']),
            models.Index(fields=['active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.generic_name} ({self.sku})"


class BatchModel(models.Model):
    """
    ORM Model for Batch (child entity of Product)
    Tracks inventory by batch with expiry dates
    """
    batch_id = models.CharField(max_length=36, unique=True, primary_key=True)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='batch_records')
    
    # Batch Information
    batch_number = models.CharField(max_length=50)
    received_date = models.DateTimeField()
    
    # Inventory Tracking
    quantity_value = models.BigIntegerField()
    quantity_unit = models.CharField(max_length=50)
    
    # Expiry & Quality
    expiry_date = models.DateField()
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pharmacy_batches'
        indexes = [
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['product']),
        ]
        unique_together = [['product', 'batch_number']]
    
    def __str__(self):
        return f"Batch {self.batch_number} - {self.product.sku}"


class InventoryLocationModel(models.Model):
    """
    ORM Model for InventoryLocation (child entity)
    Tracks physical storage locations
    """
    location_id = models.CharField(max_length=36, unique=True, primary_key=True)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='locations')
    
    # Location Information
    warehouse = models.CharField(max_length=100)
    shelf = models.CharField(max_length=50)
    row = models.CharField(max_length=50)
    column = models.CharField(max_length=50)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pharmacy_inventory_locations'
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['warehouse']),
        ]
        unique_together = [['product', 'warehouse', 'shelf', 'row', 'column']]
    
    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse}/{self.shelf}/{self.row}/{self.column}"


class DomainEventModel(models.Model):
    """
    ORM Model for Domain Event persistence
    Used for event sourcing and event-driven communication
    """
    event_id = models.CharField(max_length=36, unique=True, primary_key=True)
    product_id = models.CharField(max_length=36)  # Don't require FK, allow orphaned events
    
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField()  # Full event payload
    
    occurred_at = models.DateTimeField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pharmacy_domain_events'
        indexes = [
            models.Index(fields=['product_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['processed']),
            models.Index(fields=['occurred_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} on {self.product_id}"
