"""
Prescription Service Domain Layer - Value Objects
Prescription/Cart context for managing drug orders and prescriptions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional
from enum import Enum

from shared_ddd.base import ValueObject


class PrescriptionStatus(Enum):
    """Prescription lifecycle status"""
    DRAFT = "DRAFT"  # Being created
    SUBMITTED = "SUBMITTED"  # Sent to pharmacy
    CONFIRMED = "CONFIRMED"  # Pharmacy confirmed
    FULFILLED = "FULFILLED"  # All items dispensed
    CANCELLED = "CANCELLED"  # Prescription cancelled
    EXPIRED = "EXPIRED"  # Prescription validity expired


class CartStatus(Enum):
    """Shopping cart status"""
    ACTIVE = "ACTIVE"  # Items being added/removed
    SUBMITTED = "SUBMITTED"  # Submitted for checkout
    COMPLETED = "COMPLETED"  # Order placed
    ABANDONED = "ABANDONED"  # Cart abandoned


@dataclass(frozen=True)
class PrescriptionId(ValueObject):
    """Unique prescription identifier"""
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("PrescriptionId cannot be empty")
    
    def __str__(self):
        return self.value
    
    def equals(self, other) -> bool:
        if not isinstance(other, PrescriptionId):
            return False
        return self.value == other.value


@dataclass(frozen=True)
class CustomerId(ValueObject):
    """Reference to customer"""
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("CustomerId cannot be empty")
    
    def __str__(self):
        return self.value
    
    def equals(self, other) -> bool:
        if not isinstance(other, CustomerId):
            return False
        return self.value == other.value


@dataclass(frozen=True)
class ProductId(ValueObject):
    """Reference to pharmaceutical product"""
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("ProductId cannot be empty")
    
    def __str__(self):
        return self.value
    
    def equals(self, other) -> bool:
        if not isinstance(other, ProductId):
            return False
        return self.value == other.value


@dataclass(frozen=True)
class PrescriberInfo(ValueObject):
    """Information about prescribing doctor"""
    name: str
    license_number: str
    specialty: str = ""
    hospital: str = ""
    
    def __post_init__(self):
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Prescriber name cannot be empty")
        if not self.license_number or len(self.license_number.strip()) == 0:
            raise ValueError("License number cannot be empty")
    
    def format_info(self) -> str:
        """Format prescriber info as readable string"""
        parts = [f"{self.name} ({self.license_number})"]
        if self.specialty:
            parts.append(f"{self.specialty}")
        if self.hospital:
            parts.append(f"@ {self.hospital}")
        return " - ".join(parts)
    
    def equals(self, other) -> bool:
        if not isinstance(other, PrescriberInfo):
            return False
        return self.license_number == other.license_number


@dataclass(frozen=True)
class CartItem(ValueObject):
    """Item in prescription/cart"""
    product_id: ProductId
    sku: str
    product_name: str
    quantity: int
    unit: str = "box"
    unit_price: float = 0.0
    currency: str = "VND"
    requires_prescription: bool = False
    
    def __post_init__(self):
        if not self.sku or len(self.sku.strip()) == 0:
            raise ValueError("SKU cannot be empty")
        if not self.product_name or len(self.product_name.strip()) == 0:
            raise ValueError("Product name cannot be empty")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.unit_price < 0:
            raise ValueError("Unit price cannot be negative")
    
    def get_line_total(self) -> float:
        """Calculate total for this item"""
        return self.unit_price * self.quantity
    
    def equals(self, other) -> bool:
        if not isinstance(other, CartItem):
            return False
        return self.product_id == other.product_id and self.sku == other.sku


@dataclass(frozen=True)
class DrugRequirement(ValueObject):
    """Special requirements for drug dispensing"""
    frequency: str  # "once daily", "twice daily", etc
    duration: str  # "7 days", "30 days", etc
    dosage: str  # "500mg", "10ml", etc
    instructions: str = ""  # Special instructions
    warnings: str = ""  # Drug warnings
    
    def __post_init__(self):
        if not self.frequency or len(self.frequency.strip()) == 0:
            raise ValueError("Frequency cannot be empty")
        if not self.duration or len(self.duration.strip()) == 0:
            raise ValueError("Duration cannot be empty")
        if not self.dosage or len(self.dosage.strip()) == 0:
            raise ValueError("Dosage cannot be empty")
    
    def equals(self, other) -> bool:
        if not isinstance(other, DrugRequirement):
            return False
        return (self.frequency == other.frequency and 
                self.duration == other.duration and
                self.dosage == other.dosage)


@dataclass(frozen=True)
class Diagnosis(ValueObject):
    """Medical diagnosis information"""
    icd10_code: str  # ICD-10 code
    condition_name: str
    notes: str = ""
    
    def __post_init__(self):
        if not self.icd10_code or len(self.icd10_code.strip()) == 0:
            raise ValueError("ICD-10 code cannot be empty")
        if not self.condition_name or len(self.condition_name.strip()) == 0:
            raise ValueError("Condition name cannot be empty")
    
    def equals(self, other) -> bool:
        if not isinstance(other, Diagnosis):
            return False
        return self.icd10_code == other.icd10_code


@dataclass(frozen=True)
class PrescriptionValidity(ValueObject):
    """Prescription validity period"""
    issued_date: date
    valid_until: date
    max_refills: int = 0  # 0 = no refills
    
    def __post_init__(self):
        if self.valid_until < self.issued_date:
            raise ValueError("Validity cannot end before it starts")
        if self.max_refills < 0:
            raise ValueError("Max refills cannot be negative")
    
    def is_valid(self, check_date: date = None) -> bool:
        """Check if prescription is still valid"""
        check = check_date or date.today()
        return self.issued_date <= check <= self.valid_until
    
    def days_remaining(self, check_date: date = None) -> int:
        """Days until prescription expires"""
        check = check_date or date.today()
        if check > self.valid_until:
            return 0
        return (self.valid_until - check).days
    
    def is_expiring_soon(self, days_threshold: int = 7, check_date: date = None) -> bool:
        """Check if prescription is expiring within threshold"""
        return 0 < self.days_remaining(check_date) <= days_threshold
    
    def equals(self, other) -> bool:
        if not isinstance(other, PrescriptionValidity):
            return False
        return (self.issued_date == other.issued_date and
                self.valid_until == other.valid_until)


@dataclass(frozen=True)
class Money(ValueObject):
    """Monetary value"""
    amount: float
    currency: str = "VND"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency or len(self.currency.strip()) == 0:
            raise ValueError("Currency cannot be empty")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {other.currency} to {self.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")
        if self.amount < other.amount:
            raise ValueError("Cannot subtract more than available")
        return Money(self.amount - other.amount, self.currency)
    
    def multiply(self, factor: float) -> 'Money':
        if factor < 0:
            raise ValueError("Factor cannot be negative")
        return Money(self.amount * factor, self.currency)
    
    def __str__(self):
        return f"{self.amount:,.2f} {self.currency}"
    
    def equals(self, other) -> bool:
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency
