"""
Dispensing Service Domain Layer - Domain Events
Events for order lifecycle and state changes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from shared_ddd.base import DomainEvent


@dataclass
class OrderCreated(DomainEvent):
    """
    Event: New order created by customer
    Occurs when customer creates order with line items
    """
    order_id: str
    customer_id: str
    total_amount: float
    currency: str
    line_items_count: int
    event_type: str = field(default="OrderCreated", init=False)


@dataclass
class OrderConfirmed(DomainEvent):
    """
    Event: Order confirmed and ready for dispensing
    Occurs when customer confirms order details and payment
    """
    order_id: str
    customer_id: str
    confirmed_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="OrderConfirmed", init=False)


@dataclass
class OrderItemDispensed(DomainEvent):
    """
    Event: Order item has been dispensed
    Occurs when pharmacy staff dispenses a line item
    """
    order_id: str
    line_item_sku: str
    quantity_dispensed: int
    dispensed_by: str  # Staff member ID
    dispensed_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="OrderItemDispensed", init=False)


@dataclass
class OrderFullyDispensed(DomainEvent):
    """
    Event: All items in order have been dispensed
    Occurs when last line item is dispensed
    """
    order_id: str
    customer_id: str
    dispensed_at: datetime = field(default_factory=datetime.now)
    total_items: int = 0
    event_type: str = field(default="OrderFullyDispensed", init=False)


@dataclass
class OrderPaymentProcessed(DomainEvent):
    """
    Event: Payment for order has been processed
    Occurs when payment is successfully charged
    """
    order_id: str
    customer_id: str
    payment_method: str
    amount_paid: float
    currency: str
    transaction_id: str
    processed_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="OrderPaymentProcessed", init=False)


@dataclass
class OrderPaymentFailed(DomainEvent):
    """
    Event: Payment for order failed
    Occurs when payment processing fails
    """
    order_id: str
    customer_id: str
    payment_method: str
    attempted_amount: float
    currency: str
    failure_reason: str
    event_type: str = field(default="OrderPaymentFailed", init=False)


@dataclass
class OrderLineItemAdded(DomainEvent):
    """
    Event: New line item added to order
    Occurs when product is added to order
    """
    order_id: str
    product_id: str
    sku: str
    product_name: str
    quantity: int
    unit_price: float
    currency: str
    event_type: str = field(default="OrderLineItemAdded", init=False)


@dataclass
class OrderLineItemRemoved(DomainEvent):
    """
    Event: Line item removed from order
    Occurs when product is removed from order
    """
    order_id: str
    product_id: str
    sku: str
    quantity_removed: int
    event_type: str = field(default="OrderLineItemRemoved", init=False)


@dataclass
class OrderCancelled(DomainEvent):
    """
    Event: Order has been cancelled
    Occurs when order is cancelled by customer or system
    """
    order_id: str
    customer_id: str
    cancellation_reason: str
    cancelled_at: datetime = field(default_factory=datetime.now)
    amount_refunded: float = 0.0
    currency: str = "VND"
    event_type: str = field(default="OrderCancelled", init=False)


@dataclass
class OrderStatusChanged(DomainEvent):
    """
    Event: Order status has changed
    Generic event for order state transitions
    """
    order_id: str
    customer_id: str
    previous_status: str
    new_status: str
    changed_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="OrderStatusChanged", init=False)


@dataclass
class OrderOnHold(DomainEvent):
    """
    Event: Order placed on hold
    Occurs when order processing is temporarily suspended
    """
    order_id: str
    customer_id: str
    hold_reason: str
    placed_on_hold_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="OrderOnHold", init=False)


@dataclass
class OrderResumed(DomainEvent):
    """
    Event: Order resumed from hold
    Occurs when hold is removed and processing continues
    """
    order_id: str
    customer_id: str
    resumed_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="OrderResumed", init=False)


@dataclass
class ShippingAddressChanged(DomainEvent):
    """
    Event: Order shipping address changed
    Occurs when customer updates delivery address
    """
    order_id: str
    customer_id: str
    old_address: str
    new_address: str
    changed_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="ShippingAddressChanged", init=False)


@dataclass
class PrescriptionValidationFailed(DomainEvent):
    """
    Event: Prescription validation failed
    Occurs when prescription on order is invalid or expired
    """
    order_id: str
    customer_id: str
    prescription_id: str
    failure_reason: str
    event_type: str = field(default="PrescriptionValidationFailed", init=False)
