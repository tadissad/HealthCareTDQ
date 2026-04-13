"""
Dispensing Service Domain Layer - Value Objects
Order context: managing customer orders, line items, and dispensing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, date
from enum import Enum
from typing import List
from uuid import uuid4

from shared_ddd.base import ValueObject


class OrderStatus(Enum):
    """Order status lifecycle"""
    PENDING = "PENDING"  # Created, awaiting confirmation
    CONFIRMED = "CONFIRMED"  # Customer confirmed, ready to dispense
    DISPENSING = "DISPENSING"  # Currently being dispensed
    COMPLETED = "COMPLETED"  # Fully dispensed
    CANCELLED = "CANCELLED"  # Order cancelled
    ON_HOLD = "ON_HOLD"  # Temporarily on hold


class PaymentStatus(Enum):
    """Payment status"""
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(Enum):
    """Supported payment methods"""
    CASH = "CASH"
    CARD = "CARD"
    INSURANCE = "INSURANCE"
    BANK_TRANSFER = "BANK_TRANSFER"
    E_WALLET = "E_WALLET"


@dataclass(frozen=True)
class OrderId(ValueObject):
    """Unique order identifier"""
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("OrderId cannot be empty")
    
    def __str__(self):
        return self.value
    
    def equals(self, other) -> bool:
        if not isinstance(other, OrderId):
            return False
        return self.value == other.value


@dataclass(frozen=True)
class CustomerId(ValueObject):
    """Reference to customer placing order"""
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
    """Reference to product in order"""
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
class Money(ValueObject):
    """Monetary value with currency"""
    amount: float
    currency: str = "VND"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency or len(self.currency.strip()) == 0:
            raise ValueError("Currency cannot be empty")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")
        if self.amount < other.amount:
            raise ValueError("Cannot subtract more than available amount")
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


@dataclass(frozen=True)
class Quantity(ValueObject):
    """Quantity of items with unit"""
    value: int
    unit: str = "box"
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Quantity cannot be negative")
        if not self.unit or len(self.unit.strip()) == 0:
            raise ValueError("Unit cannot be empty")
    
    def add(self, other: 'Quantity') -> 'Quantity':
        if self.unit != other.unit:
            raise ValueError(f"Cannot add {other.unit} to {self.unit}")
        return Quantity(self.value + other.value, self.unit)
    
    def subtract(self, other: 'Quantity') -> 'Quantity':
        if self.unit != other.unit:
            raise ValueError(f"Cannot subtract {other.unit} from {self.unit}")
        if self.value < other.value:
            raise ValueError("Cannot subtract more than available quantity")
        return Quantity(self.value - other.value, self.unit)
    
    def __str__(self):
        return f"{self.value} {self.unit}"
    
    def equals(self, other) -> bool:
        if not isinstance(other, Quantity):
            return False
        return self.value == other.value and self.unit == other.unit


@dataclass(frozen=True)
class LineItem(ValueObject):
    """Item in order with pricing"""
    product_id: ProductId
    sku: str
    product_name: str
    quantity: Quantity
    unit_price: Money
    line_total: Money  # unit_price * quantity
    
    def __post_init__(self):
        if not self.sku or len(self.sku.strip()) == 0:
            raise ValueError("SKU cannot be empty")
        if not self.product_name or len(self.product_name.strip()) == 0:
            raise ValueError("Product name cannot be empty")
        
        if self.quantity.unit != self.unit_price.currency:
            # Validate that line_total is correct
            expected_total = self.unit_price.amount * self.quantity.value
            if abs(self.line_total.amount - expected_total) > 0.01:
                raise ValueError("Line total does not match unit price × quantity")
    
    def get_discount_applied(self, original_price: Money) -> Money:
        """Calculate discount between original price and actual unit price"""
        if original_price.amount < self.unit_price.amount:
            return Money(0, original_price.currency)
        return Money(original_price.amount - self.unit_price.amount, original_price.currency)
    
    def equals(self, other) -> bool:
        if not isinstance(other, LineItem):
            return False
        return (self.product_id == other.product_id and 
                self.quantity == other.quantity and
                self.unit_price == other.unit_price)


@dataclass(frozen=True)
class ShippingAddress(ValueObject):
    """Where order will be shipped"""
    street: str
    city: str
    district: str
    postal_code: str
    country: str = "Vietnam"
    notes: str = ""
    
    def __post_init__(self):
        if not self.street or len(self.street.strip()) == 0:
            raise ValueError("Street cannot be empty")
        if not self.city or len(self.city.strip()) == 0:
            raise ValueError("City cannot be empty")
        if not self.district or len(self.district.strip()) == 0:
            raise ValueError("District cannot be empty")
        if not self.postal_code or len(self.postal_code.strip()) == 0:
            raise ValueError("Postal code cannot be empty")
    
    def format_address(self) -> str:
        """Format address as readable string"""
        return f"{self.street}, {self.district}, {self.city}, {self.postal_code}, {self.country}"
    
    def equals(self, other) -> bool:
        if not isinstance(other, ShippingAddress):
            return False
        return (self.street == other.street and 
                self.city == other.city and
                self.district == other.district and
                self.postal_code == other.postal_code and
                self.country == other.country)


@dataclass(frozen=True)
class PaymentInfo(ValueObject):
    """Payment details for order"""
    method: PaymentMethod
    status: PaymentStatus
    transaction_id: str = ""
    reference_number: str = ""
    
    def __post_init__(self):
        if not isinstance(self.method, PaymentMethod):
            raise ValueError("Invalid payment method")
        if not isinstance(self.status, PaymentStatus):
            raise ValueError("Invalid payment status")
    
    def equals(self, other) -> bool:
        if not isinstance(other, PaymentInfo):
            return False
        return (self.method == other.method and 
                self.status == other.status and
                self.transaction_id == other.transaction_id)


@dataclass(frozen=True)
class PrescriptionInfo(ValueObject):
    """Prescription reference for order"""
    prescription_id: str
    prescriber_name: str
    prescription_date: date
    valid_until: date
    
    def __post_init__(self):
        if not self.prescription_id or len(self.prescription_id.strip()) == 0:
            raise ValueError("Prescription ID cannot be empty")
        if not self.prescriber_name or len(self.prescriber_name.strip()) == 0:
            raise ValueError("Prescriber name cannot be empty")
        if self.valid_until < self.prescription_date:
            raise ValueError("Prescription validity cannot end before it starts")
    
    def is_valid(self, reference_date: date = None) -> bool:
        """Check if prescription is still valid"""
        check_date = reference_date or date.today()
        return self.prescription_date <= check_date <= self.valid_until
    
    def days_until_expiry(self, reference_date: date = None) -> int:
        """Days until prescription expires"""
        check_date = reference_date or date.today()
        if check_date > self.valid_until:
            return 0
        return (self.valid_until - check_date).days
    
    def equals(self, other) -> bool:
        if not isinstance(other, PrescriptionInfo):
            return False
        return self.prescription_id == other.prescription_id
