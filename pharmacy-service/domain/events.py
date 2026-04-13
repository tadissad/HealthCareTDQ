"""
Pharmacy Domain Events
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared_ddd.base import DomainEvent


@dataclass
class ProductAdded(DomainEvent):
    """Event: New product added to pharmacy catalog"""
    product_id: str
    sku: str
    name: str
    manufacturer: str
    event_type: str = "product.added"


@dataclass
class ProductPriceChanged(DomainEvent):
    """Event: Product price changed"""
    product_id: str
    old_price: float
    new_price: float
    changed_by: str
    event_type: str = "product.price_changed"


@dataclass
class InventoryAdjusted(DomainEvent):
    """Event: Inventory quantity adjusted"""
    product_id: str
    old_quantity: int
    new_quantity: int
    reason: str  # received, sold, damaged, expired, adjustment
    event_type: str = "inventory.adjusted"


@dataclass
class LowStockAlert(DomainEvent):
    """Event: Product stock below threshold"""
    product_id: str
    current_quantity: int
    threshold: int
    sku: str
    event_type: str = "inventory.low_stock"


@dataclass
class ProductExpiring(DomainEvent):
    """Event: Product approaching expiry date"""
    product_id: str
    batch_number: str
    expiry_date: datetime
    days_until_expiry: int
    quantity_expiring: int
    event_type: str = "product.expiring"


@dataclass
class ProductExpired(DomainEvent):
    """Event: Product batch has expired"""
    product_id: str
    batch_number: str
    quantity_expired: int
    event_type: str = "product.expired"


@dataclass
class ManufacturerChanged(DomainEvent):
    """Event: Manufacturer changed for product"""
    product_id: str
    old_manufacturer: str
    new_manufacturer: str
    event_type: str = "product.manufacturer_changed"


@dataclass
class ProductCategoryChanged(DomainEvent):
    """Event: Product category changed"""
    product_id: str
    old_category: str
    new_category: str
    event_type: str = "product.category_changed"


@dataclass
class PrescriptionRequirementChanged(DomainEvent):
    """Event: Prescription requirement changed"""
    product_id: str
    requires_prescription: bool
    event_type: str = "product.prescription_requirement_changed"


@dataclass
class BatchAdded(DomainEvent):
    """Event: New batch received for product"""
    product_id: str
    batch_number: str
    quantity_received: int
    expiry_date: datetime
    event_type: str = "product.batch_added"
