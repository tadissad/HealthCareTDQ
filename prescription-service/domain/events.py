"""
Prescription Service Domain Layer - Domain Events
Events for prescription lifecycle
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from shared_ddd.base import DomainEvent


@dataclass
class PrescriptionCreated(DomainEvent):
    """Event: New prescription created"""
    prescription_id: str
    customer_id: str
    prescriber_name: str
    diagnosis: str
    items_count: int
    event_type: str = field(default="PrescriptionCreated", init=False)


@dataclass
class PrescriptionItemAdded(DomainEvent):
    """Event: Drug item added to prescription"""
    prescription_id: str
    product_id: str
    sku: str
    product_name: str
    quantity: int
    unit_price: float
    currency: str
    event_type: str = field(default="PrescriptionItemAdded", init=False)


@dataclass
class PrescriptionItemRemoved(DomainEvent):
    """Event: Drug item removed from prescription"""
    prescription_id: str
    product_id: str
    sku: str
    quantity_removed: int
    event_type: str = field(default="PrescriptionItemRemoved", init=False)


@dataclass
class PrescriptionItemQuantityChanged(DomainEvent):
    """Event: Quantity changed for prescription item"""
    prescription_id: str
    product_id: str
    old_quantity: int
    new_quantity: int
    event_type: str = field(default="PrescriptionItemQuantityChanged", init=False)


@dataclass
class PrescriptionSubmitted(DomainEvent):
    """Event: Prescription submitted for dispensing"""
    prescription_id: str
    customer_id: str
    total_amount: float
    currency: str
    items_count: int
    submitted_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="PrescriptionSubmitted", init=False)


@dataclass
class PrescriptionConfirmed(DomainEvent):
    """Event: Pharmacy confirmed prescription"""
    prescription_id: str
    customer_id: str
    confirmed_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="PrescriptionConfirmed", init=False)


@dataclass
class PrescriptionFulfilled(DomainEvent):
    """Event: All prescription items dispensed"""
    prescription_id: str
    customer_id: str
    fulfilled_at: datetime = field(default_factory=datetime.now)
    total_items: int = 0
    event_type: str = field(default="PrescriptionFulfilled", init=False)


@dataclass
class PrescriptionCancelled(DomainEvent):
    """Event: Prescription cancelled"""
    prescription_id: str
    customer_id: str
    cancellation_reason: str
    cancelled_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="PrescriptionCancelled", init=False)


@dataclass
class PrescriptionExpired(DomainEvent):
    """Event: Prescription validity expired"""
    prescription_id: str
    customer_id: str
    expiry_date: str
    event_type: str = field(default="PrescriptionExpired", init=False)


@dataclass
class PrescriptionValidationFailed(DomainEvent):
    """Event: Prescription validation failed"""
    prescription_id: str
    customer_id: str
    failure_reason: str
    event_type: str = field(default="PrescriptionValidationFailed", init=False)


@dataclass
class CartCreated(DomainEvent):
    """Event: Shopping cart created"""
    prescription_id: str
    customer_id: str
    event_type: str = field(default="CartCreated", init=False)


@dataclass
class CartItemAdded(DomainEvent):
    """Event: Item added to cart"""
    prescription_id: str
    product_id: str
    sku: str
    quantity: int
    event_type: str = field(default="CartItemAdded", init=False)


@dataclass
class CartCleared(DomainEvent):
    """Event: Cart items cleared"""
    prescription_id: str
    items_count: int
    event_type: str = field(default="CartCleared", init=False)


@dataclass
class CartTotalCalculated(DomainEvent):
    """Event: Cart total recalculated"""
    prescription_id: str
    total_amount: float
    currency: str
    items_count: int
    event_type: str = field(default="CartTotalCalculated", init=False)


@dataclass
class PrescriptionRequirementValidated(DomainEvent):
    """Event: Drug requirements validated"""
    prescription_id: str
    product_id: str
    sku: str
    validation_result: str  # VALID or INVALID
    warnings: str = ""
    event_type: str = field(default="PrescriptionRequirementValidated", init=False)
