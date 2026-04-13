"""
Prescription Service Infrastructure Layer - ORM Models
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
import json
from datetime import datetime


class PrescriptionModel(models.Model):
    """ORM Model for Prescription Aggregate Root"""
    
    # Identity
    prescription_id = models.CharField(
        max_length=36, unique=True, primary_key=True, editable=False
    )
    customer_id = models.CharField(max_length=36, db_index=True)
    
    # Prescriber Information
    prescriber_name = models.CharField(max_length=255)
    prescriber_license_number = models.CharField(max_length=50)
    prescriber_specialty = models.CharField(max_length=100)
    prescriber_hospital = models.CharField(max_length=255)
    
    # Diagnoses (stored as JSON)
    diagnoses_json = models.TextField(
        default="[]",
        help_text="JSON array of diagnoses: [{icd_code, condition_name}]"
    )
    
    # Validity information
    issued_date = models.DateTimeField(auto_now_add=True, db_index=True)
    valid_until = models.DateTimeField(db_index=True)
    max_refills = models.IntegerField(default=3)
    
    # Status tracking
    prescription_status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('SUBMITTED', 'Submitted'),
            ('CONFIRMED', 'Confirmed'),
            ('FULFILLED', 'Fulfilled'),
            ('CANCELLED', 'Cancelled'),
            ('EXPIRED', 'Expired'),
        ],
        default='DRAFT',
        db_index=True
    )
    cart_status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('SUBMITTED', 'Submitted'),
            ('COMPLETED', 'Completed'),
            ('ABANDONED', 'Abandoned'),
        ],
        default='ACTIVE'
    )
    
    # Financial tracking
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='VND')
    
    # Timestamps for state changes
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    submitted_date = models.DateTimeField(null=True, blank=True)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    fulfilled_date = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'prescription_prescription'
        indexes = [
            models.Index(fields=['customer_id', 'prescription_status']),
            models.Index(fields=['prescription_status', 'created_at']),
            models.Index(fields=['valid_until']),
        ]
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'
    
    def __str__(self):
        return f"Prescription {self.prescription_id}"
    
    def get_diagnostics(self):
        """Parse diagnoses JSON"""
        try:
            return json.loads(self.diagnoses_json)
        except:
            return []
    
    def set_diagnostics(self, diagnoses):
        """Store diagnoses as JSON"""
        self.diagnoses_json = json.dumps(diagnoses)


class PrescriptionLineItemModel(models.Model):
    """ORM Model for Prescription Line Item (child entity)"""
    
    id = models.AutoField(primary_key=True)
    prescription = models.ForeignKey(
        PrescriptionModel,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    
    # Product information
    product_id = models.CharField(max_length=36, db_index=True)
    sku = models.CharField(max_length=50)
    product_name = models.CharField(max_length=255)
    
    # Quantity and pricing
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='VND')
    requires_prescription = models.BooleanField(default=True)
    
    # Drug requirement information (stored as JSON)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    instructions = models.TextField()
    warnings = models.TextField()
    
    # Fulfillment tracking
    fulfill_quantity = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prescription_line_item'
        indexes = [
            models.Index(fields=['prescription', 'product_id']),
        ]
        verbose_name = 'Prescription Line Item'
        verbose_name_plural = 'Prescription Line Items'
    
    def __str__(self):
        return f"Item {self.product_id} - {self.product_name}"


class DomainEventModel(models.Model):
    """ORM Model for storing domain events"""
    
    id = models.AutoField(primary_key=True)
    
    # Event identity
    event_id = models.CharField(max_length=36, unique=True, db_index=True)
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Event class name (e.g., PrescriptionCreated)"
    )
    
    # Aggregate relationship
    aggregate_id = models.CharField(max_length=36, db_index=True)
    aggregate_type = models.CharField(
        max_length=50,
        default='Prescription',
        help_text="Type of aggregate (e.g., Prescription)"
    )
    
    # Event data (stored as JSON)
    event_data = models.TextField(
        help_text="Complete event data as JSON"
    )
    
    # Metadata
    occurred_at = models.DateTimeField(db_index=True)
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'prescription_domain_event'
        indexes = [
            models.Index(fields=['aggregate_id', 'occurred_at']),
            models.Index(fields=['event_type', 'recorded_at']),
        ]
        verbose_name = 'Domain Event'
        verbose_name_plural = 'Domain Events'
        ordering = ['occurred_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.aggregate_id}"
