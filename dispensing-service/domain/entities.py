"""
Dispensing Service Domain Layer - Entities
Order aggregate and its child entities
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional
from uuid import uuid4

from shared_ddd.base import Entity, Aggregate
from .value_objects import (
    OrderId, CustomerId, ProductId, Money, Quantity, LineItem,
    ShippingAddress, PaymentInfo, PrescriptionInfo, PaymentStatus,
    OrderStatus, PaymentMethod
)
from .events import (
    OrderCreated, OrderConfirmed, OrderItemDispensed, OrderFullyDispensed,
    OrderPaymentProcessed, OrderPaymentFailed, OrderLineItemAdded,
    OrderLineItemRemoved, OrderCancelled, OrderStatusChanged, OrderOnHold,
    OrderResumed, ShippingAddressChanged, PrescriptionValidationFailed
)


@dataclass
class OrderItem(Entity):
    """
    Child entity: Represents line item in order
    Tracks individual product with quantity and pricing
    """
    order_item_id: str = field(default_factory=lambda: str(uuid4()))
    line_item: LineItem = None
    dispensed_quantity: Quantity = None
    notes: str = ""
    
    def __post_init__(self):
        if self.dispensed_quantity is None:
            self.dispensed_quantity = Quantity(0, self.line_item.quantity.unit)
    
    def dispense(self, quantity: Quantity) -> None:
        """Dispense portion of line item"""
        if quantity.unit != self.line_item.quantity.unit:
            raise ValueError(f"Cannot dispense {quantity.unit} from {self.line_item.quantity.unit}")
        
        new_dispensed = self.dispensed_quantity.add(quantity)
        if new_dispensed.value > self.line_item.quantity.value:
            raise ValueError("Cannot dispense more than ordered quantity")
        
        self.dispensed_quantity = new_dispensed
    
    def remaining_quantity(self) -> Quantity:
        """Get remaining quantity to dispense"""
        return self.line_item.quantity.subtract(self.dispensed_quantity)
    
    def is_fully_dispensed(self) -> bool:
        """Check if all items have been dispensed"""
        return self.dispensed_quantity.value == self.line_item.quantity.value
    
    def get_dispersed_total(self) -> Money:
        """Calculate value of dispensed items"""
        ratio = self.dispensed_quantity.value / self.line_item.quantity.value
        return self.line_item.unit_price.multiply(ratio * self.dispensed_quantity.value)


@dataclass
class Order(Aggregate):
    """
    Aggregate Root: Order
    Manages customer order lifecycle from creation through dispensing
    
    Responsibilities:
    - Maintain order line items and their dispensing state
    - Track payment status and transactions
    - Manage order status transitions
    - Validate order state changes
    - Raise domain events for order events
    """
    order_id: OrderId = None
    customer_id: CustomerId = None
    order_items: List[OrderItem] = field(default_factory=list)
    
    status: OrderStatus = OrderStatus.PENDING
    payment_info: PaymentInfo = None
    prescription_info: Optional[PrescriptionInfo] = None
    shipping_address: Optional[ShippingAddress] = None
    
    order_date: datetime = field(default_factory=datetime.now)
    confirmed_date: Optional[datetime] = None
    dispensed_date: Optional[datetime] = None
    
    total_amount: Money = None
    discount_amount: Money = field(default_factory=lambda: Money(0, "VND"))
    notes: str = ""
    
    # Child entities
    _events: List = field(default_factory=list)
    
    def __post_init__(self):
        if self.total_amount is None:
            self.total_amount = Money(0, "VND")
    
    def get_subtotal(self) -> Money:
        """Calculate subtotal of all line items"""
        if not self.order_items:
            return Money(0, "VND")
        
        subtotal = Money(0, self.order_items[0].line_item.unit_price.currency)
        for item in self.order_items:
            subtotal = subtotal.add(item.line_item.line_total)
        return subtotal
    
    def get_total_after_discount(self) -> Money:
        """Calculate total after applying discount"""
        subtotal = self.get_subtotal()
        return subtotal.subtract(self.discount_amount)
    
    def add_line_item(self, line_item: LineItem) -> None:
        """Add product line item to order"""
        if self.status == OrderStatus.COMPLETED:
            raise ValueError("Cannot add items to completed order")
        if self.status == OrderStatus.CANCELLED:
            raise ValueError("Cannot add items to cancelled order")
        
        # Check if product already in order
        for item in self.order_items:
            if item.line_item.product_id == line_item.product_id:
                raise ValueError("Product already in order")
        
        order_item = OrderItem(line_item=line_item)
        self.order_items.append(order_item)
        
        # Update total
        self.total_amount = self.total_amount.add(line_item.line_total)
        
        # Raise event
        self.add_event(OrderLineItemAdded(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            product_id=str(line_item.product_id),
            sku=line_item.sku,
            product_name=line_item.product_name,
            quantity=line_item.quantity.value,
            unit_price=line_item.unit_price.amount,
            currency=line_item.unit_price.currency,
        ))
    
    def remove_line_item(self, product_id: ProductId) -> None:
        """Remove line item from order"""
        if self.status == OrderStatus.COMPLETED:
            raise ValueError("Cannot remove items from completed order")
        if self.status == OrderStatus.CANCELLED:
            raise ValueError("Cannot remove items from cancelled order")
        
        for i, item in enumerate(self.order_items):
            if item.line_item.product_id == product_id:
                removed_item = self.order_items.pop(i)
                
                # Update total
                self.total_amount = self.total_amount.subtract(removed_item.line_item.line_total)
                
                # Raise event
                self.add_event(OrderLineItemRemoved(
                    aggregate_id=str(self.order_id),
                    order_id=str(self.order_id),
                    product_id=str(product_id),
                    sku=removed_item.line_item.sku,
                    quantity_removed=removed_item.line_item.quantity.value,
                ))
                return
        
        raise ValueError(f"Product {product_id} not in order")
    
    def confirm_order(self) -> None:
        """Confirm order and prepare for dispensing"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order in {self.status.value} status")
        
        if not self.order_items:
            raise ValueError("Cannot confirm empty order")
        
        if self.payment_info.status != PaymentStatus.PAID:
            raise ValueError("Cannot confirm order without payment")
        
        if self.prescription_info and not self.prescription_info.is_valid():
            self.add_event(PrescriptionValidationFailed(
                aggregate_id=str(self.order_id),
                order_id=str(self.order_id),
                customer_id=str(self.customer_id),
                prescription_id=self.prescription_info.prescription_id,
                failure_reason="Prescription expired",
            ))
            raise ValueError("Prescription expired")
        
        old_status = self.status
        self.status = OrderStatus.CONFIRMED
        self.confirmed_date = datetime.now()
        
        self.add_event(OrderConfirmed(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            customer_id=str(self.customer_id),
        ))
        
        self.add_event(OrderStatusChanged(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            customer_id=str(self.customer_id),
            previous_status=old_status.value,
            new_status=self.status.value,
        ))
    
    def dispense_item(self, product_id: ProductId, quantity: Quantity, dispensed_by: str) -> None:
        """Dispense ordered item"""
        if self.status not in [OrderStatus.CONFIRMED, OrderStatus.DISPENSING]:
            raise ValueError(f"Cannot dispense in {self.status.value} status")
        
        # Find order item
        order_item = None
        for item in self.order_items:
            if item.line_item.product_id == product_id:
                order_item = item
                break
        
        if not order_item:
            raise ValueError(f"Product {product_id} not in order")
        
        # Dispense
        order_item.dispense(quantity)
        
        if self.status == OrderStatus.CONFIRMED:
            self.status = OrderStatus.DISPENSING
        
        # Raise event
        self.add_event(OrderItemDispensed(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            line_item_sku=order_item.line_item.sku,
            quantity_dispensed=quantity.value,
            dispensed_by=dispensed_by,
        ))
        
        # Check if fully dispensed
        if all(item.is_fully_dispensed() for item in self.order_items):
            self.status = OrderStatus.COMPLETED
            self.dispensed_date = datetime.now()
            
            self.add_event(OrderFullyDispensed(
                aggregate_id=str(self.order_id),
                order_id=str(self.order_id),
                customer_id=str(self.customer_id),
                total_items=len(self.order_items),
            ))
            
            self.add_event(OrderStatusChanged(
                aggregate_id=str(self.order_id),
                order_id=str(self.order_id),
                customer_id=str(self.customer_id),
                previous_status="DISPENSING",
                new_status="COMPLETED",
            ))
    
    def mark_payment_processed(self, transaction_id: str, reference_number: str = "") -> None:
        """Record successful payment"""
        old_status = self.payment_info.status
        
        # Update payment info
        from .value_objects import PaymentInfo
        self.payment_info = PaymentInfo(
            method=self.payment_info.method,
            status=PaymentStatus.PAID,
            transaction_id=transaction_id,
            reference_number=reference_number,
        )
        
        self.add_event(OrderPaymentProcessed(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            customer_id=str(self.customer_id),
            payment_method=self.payment_info.method.value,
            amount_paid=self.total_amount.amount,
            currency=self.total_amount.currency,
            transaction_id=transaction_id,
        ))
    
    def mark_payment_failed(self, reason: str) -> None:
        """Record payment failure"""
        old_status = self.payment_info.status
        
        from .value_objects import PaymentInfo
        self.payment_info = PaymentInfo(
            method=self.payment_info.method,
            status=PaymentStatus.FAILED,
        )
        
        self.add_event(OrderPaymentFailed(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            customer_id=str(self.customer_id),
            payment_method=self.payment_info.method.value,
            attempted_amount=self.total_amount.amount,
            currency=self.total_amount.currency,
            failure_reason=reason,
        ))
    
    def cancel_order(self, reason: str = "") -> None:
        """Cancel order"""
        if self.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel order in {self.status.value} status")
        
        old_status = self.status
        self.status = OrderStatus.CANCELLED
        
        refund_amount = self.total_amount.amount if self.payment_info.status == PaymentStatus.PAID else 0.0
        
        self.add_event(OrderCancelled(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            customer_id=str(self.customer_id),
            cancellation_reason=reason,
            amount_refunded=refund_amount,
            currency=self.total_amount.currency,
        ))
        
        self.add_event(OrderStatusChanged(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            customer_id=str(self.customer_id),
            previous_status=old_status.value,
            new_status="CANCELLED",
        ))
    
    def put_on_hold(self, reason: str) -> None:
        """Temporarily suspend order processing"""
        if self.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise ValueError(f"Cannot hold completed or cancelled order")
        
        old_status = self.status
        self.status = OrderStatus.ON_HOLD
        
        self.add_event(OrderOnHold(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            customer_id=str(self.customer_id),
            hold_reason=reason,
        ))
    
    def resume_from_hold(self) -> None:
        """Resume order from hold"""
        if self.status != OrderStatus.ON_HOLD:
            raise ValueError("Order is not on hold")
        
        self.status = OrderStatus.CONFIRMED
        
        self.add_event(OrderResumed(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            customer_id=str(self.customer_id),
        ))
    
    def update_shipping_address(self, new_address: ShippingAddress) -> None:
        """Update delivery address"""
        if self.status in [OrderStatus.DISPENSING, OrderStatus.COMPLETED]:
            raise ValueError("Cannot change address after dispensing started")
        
        old_address = self.shipping_address
        self.shipping_address = new_address
        
        self.add_event(ShippingAddressChanged(
            aggregate_id=str(self.order_id),
            order_id=str(self.order_id),
            customer_id=str(self.customer_id),
            old_address=old_address.format_address() if old_address else "Not set",
            new_address=new_address.format_address(),
        ))
    
    def get_dispensed_total(self) -> Money:
        """Calculate total value of dispensed items"""
        if not self.order_items:
            return Money(0, self.total_amount.currency)
        
        total = Money(0, self.total_amount.currency)
        for item in self.order_items:
            total = total.add(item.get_dispersed_total())
        return total
    
    def is_partially_dispensed(self) -> bool:
        """Check if some but not all items dispensed"""
        return any(item.dispensed_quantity.value > 0 for item in self.order_items) and \
               not all(item.is_fully_dispensed() for item in self.order_items)
