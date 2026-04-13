"""
Pharmacy Domain - Value Objects

Dược phẩm và thiết bị y tế là core của pharmacy service
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re

from shared_ddd.base import ValueObject, InvalidValueObjectException


@dataclass
class ProductId(ValueObject):
    """Unique identifier for a product"""
    value: str
    
    def equals(self, other: "ProductId") -> bool:
        return self.value == other.value
    
    def __str__(self):
        return self.value


@dataclass
class SKU(ValueObject):
    """Stock Keeping Unit - unique product code"""
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value) < 3:
            raise InvalidValueObjectException(f"Invalid SKU: {self.value}")
    
    def equals(self, other: "SKU") -> bool:
        return self.value.upper() == other.value.upper()


@dataclass
class Price(ValueObject):
    """Product price"""
    amount: float
    currency: str = "VND"
    
    def __post_init__(self):
        if self.amount < 0:
            raise InvalidValueObjectException(f"Invalid price: {self.amount}")
    
    def equals(self, other: "Price") -> bool:
        return self.amount == other.amount and self.currency == other.currency
    
    def apply_discount(self, discount_percent: float) -> "Price":
        """Apply discount to price"""
        if not (0 <= discount_percent <= 100):
            raise InvalidValueObjectException(f"Invalid discount: {discount_percent}")
        discounted = self.amount * (1 - discount_percent / 100)
        return Price(discounted, self.currency)


@dataclass
class Quantity(ValueObject):
    """Stock quantity"""
    value: int
    unit: str = "box"  # box, tablet, ml, etc.
    
    def __post_init__(self):
        if self.value < 0:
            raise InvalidValueObjectException(f"Invalid quantity: {self.value}")
    
    def equals(self, other: "Quantity") -> bool:
        return self.value == other.value and self.unit == other.unit
    
    def add(self, qty: int) -> "Quantity":
        """Add to quantity"""
        return Quantity(self.value + qty, self.unit)
    
    def subtract(self, qty: int) -> "Quantity":
        """Subtract from quantity"""
        new_val = self.value - qty
        if new_val < 0:
            raise InvalidValueObjectException(f"Cannot go below 0")
        return Quantity(new_val, self.unit)
    
    def is_low_stock(self, threshold: int) -> bool:
        """Check if below threshold"""
        return self.value <= threshold


@dataclass
class ExpiryDate(ValueObject):
    """Product expiry date"""
    value: datetime
    
    def __post_init__(self):
        if self.value <= datetime.now():
            raise InvalidValueObjectException(f"Expiry date is in the past: {self.value}")
    
    def equals(self, other: "ExpiryDate") -> bool:
        return self.value == other.value
    
    def is_expired(self) -> bool:
        """Check if product is expired"""
        return datetime.now() >= self.value
    
    def days_until_expiry(self) -> int:
        """Days until expiry"""
        delta = self.value - datetime.now()
        return delta.days


@dataclass
class BatchNumber(ValueObject):
    """Batch/Lot number for tracking"""
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value) < 2:
            raise InvalidValueObjectException(f"Invalid batch number: {self.value}")
    
    def equals(self, other: "BatchNumber") -> bool:
        return self.value.upper() == other.value.upper()


@dataclass
class DosageStrength(ValueObject):
    """Medication dosage/strength"""
    value: str  # e.g., "500mg", "250mg/5ml", "10units/ml"
    
    def __post_init__(self):
        if not self.value:
            raise InvalidValueObjectException("Invalid dosage strength")
    
    def equals(self, other: "DosageStrength") -> bool:
        return self.value.lower() == other.value.lower()
    
    def __str__(self):
        return self.value


@dataclass
class DosageForm(ValueObject):
    """Medication form"""
    value: str  # tablet, capsule, injectable, infusion, oral solution, etc.
    
    VALID_FORMS = {
        "tablet", "capsule", "injectable", "infusion", "oral solution", 
        "powder", "cream", "ointment", "suspension", "syrup", "patch"
    }
    
    def __post_init__(self):
        if self.value.lower() not in self.VALID_FORMS:
            raise InvalidValueObjectException(f"Invalid dosage form: {self.value}")
    
    def equals(self, other: "DosageForm") -> bool:
        return self.value.lower() == other.value.lower()


@dataclass
class ManufacturerInfo(ValueObject):
    """Manufacturer information"""
    name: str
    country: str
    registration_code: Optional[str] = None  # Registration/approval code
    
    def __post_init__(self):
        if not self.name or not self.country:
            raise InvalidValueObjectException("Manufacturer name and country required")
    
    def equals(self, other: "ManufacturerInfo") -> bool:
        return (self.name.lower() == other.name.lower() and 
                self.country.lower() == other.country.lower())


@dataclass
class ATCCode(ValueObject):
    """ATC (Anatomical Therapeutic Chemical) Classification"""
    value: str  # e.g., "A01AD05"
    
    def __post_init__(self):
        # Basic ATC format validation
        if not re.match(r'^[A-Z]\d{2}[A-Z]{2}\d{2}$', self.value):
            raise InvalidValueObjectException(f"Invalid ATC code: {self.value}")
    
    def equals(self, other: "ATCCode") -> bool:
        return self.value.upper() == other.value.upper()
    
    def get_main_group(self) -> str:
        """Get main ATC classification group"""
        return self.value[0]  # First letter


@dataclass
class ICDCode(ValueObject):
    """ICD-10 diagnosis code"""
    value: str  # e.g., "I10"
    
    def __post_init__(self):
        if not self.value or len(self.value) < 2:
            raise InvalidValueObjectException(f"Invalid ICD code: {self.value}")
    
    def equals(self, other: "ICDCode") -> bool:
        return self.value.upper() == other.value.upper()


@dataclass
class PrescriptionRequirement(ValueObject):
    """Whether product requires prescription"""
    requires_prescription: bool
    max_quantity_per_purchase: Optional[int] = None
    
    def equals(self, other: "PrescriptionRequirement") -> bool:
        return (self.requires_prescription == other.requires_prescription and
                self.max_quantity_per_purchase == other.max_quantity_per_purchase)
