"""
Dispensing Service Application Layer - Commands
CQRS: Commands represent state-changing operations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import date


@dataclass
class CreateOrderCommand:
    """Command: Create new customer order"""
    customer_id: str
    line_items: List[Dict[str, Any]]  # [{product_id, sku, name, quantity, unit_price, unit, currency}]
    payment_method: str  # CASH, CARD, INSURANCE, BANK_TRANSFER, E_WALLET
    shipping_address: Optional[Dict[str, str]] = None  # {street, city, district, postal_code, country, notes}
    prescription_id: Optional[str] = None
    prescription_info: Optional[Dict[str, Any]] = None  # {prescriber_name, prescription_date, valid_until}
    notes: Optional[str] = None


@dataclass
class ConfirmOrderCommand:
    """Command: Confirm order ready for dispensing"""
    order_id: str
    payment_authorized: bool = False  # Has payment been authorized?
    transaction_id: Optional[str] = None


@dataclass
class DispenseOrderItemCommand:
    """Command: Dispense item from order"""
    order_id: str
    product_id: str
    quantity: int
    unit: str = "box"
    dispensed_by: str = "SYSTEM"


@dataclass
class ProcessPaymentCommand:
    """Command: Process payment for order"""
    order_id: str
    payment_method: str
    amount: float
    transaction_id: str
    reference_number: Optional[str] = None


@dataclass
class HandlePaymentFailureCommand:
    """Command: Record payment failure"""
    order_id: str
    failure_reason: str
    attempted_amount: float
    payment_method: str


@dataclass
class CancelOrderCommand:
    """Command: Cancel order"""
    order_id: str
    cancellation_reason: str


@dataclass
class PutOrderOnHoldCommand:
    """Command: Temporarily suspend order"""
    order_id: str
    hold_reason: str


@dataclass
class ResumeOrderCommand:
    """Command: Resume order from hold"""
    order_id: str


@dataclass
class UpdateShippingAddressCommand:
    """Command: Update order shipping address"""
    order_id: str
    street: str
    city: str
    district: str
    postal_code: str
    country: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class RemoveOrderLineItemCommand:
    """Command: Remove item from order"""
    order_id: str
    product_id: str


@dataclass
class ApplyDiscountToOrderCommand:
    """Command: Apply discount to order"""
    order_id: str
    discount_percent: float
    reason: str = "Customer discount"


@dataclass
class ValidatePrescriptionCommand:
    """Command: Validate prescription for order"""
    order_id: str
