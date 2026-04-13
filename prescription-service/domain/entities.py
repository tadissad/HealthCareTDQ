"""
Prescription Service Domain Layer - Entities
Prescription aggregate and child entities
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
    PrescriptionId, CustomerId, ProductId, CartItem, PrescriberInfo,
    DrugRequirement, Diagnosis, PrescriptionValidity, PrescriptionStatus,
    CartStatus, Money
)
from .events import (
    PrescriptionCreated, PrescriptionItemAdded, PrescriptionItemRemoved,
    PrescriptionItemQuantityChanged, PrescriptionSubmitted, PrescriptionConfirmed,
    PrescriptionFulfilled, PrescriptionCancelled, PrescriptionExpired,
    PrescriptionValidationFailed, CartCreated, CartItemAdded, CartCleared,
    CartTotalCalculated, PrescriptionRequirementValidated
)


@dataclass
class PrescriptionLineItem(Entity):
    """
    Child entity: Line item in prescription
    Represents one drug with dosage requirements
    """
    item_id: str = field(default_factory=lambda: str(uuid4()))
    cart_item: CartItem = None
    drug_requirement: DrugRequirement = None
    fulfilled_quantity: int = 0
    
    def fulfill(self, quantity: int) -> None:
        """Mark item quantity as fulfilled"""
        if quantity < 0:
            raise ValueError("Fulfilled quantity cannot be negative")
        if quantity > self.cart_item.quantity:
            raise ValueError("Cannot fulfill more than ordered")
        self.fulfilled_quantity = quantity
    
    def remaining_quantity(self) -> int:
        """Get remaining quantity to fulfill"""
        return self.cart_item.quantity - self.fulfilled_quantity
    
    def is_fully_fulfilled(self) -> bool:
        """Check if all items fulfilled"""
        return self.fulfilled_quantity == self.cart_item.quantity
    
    def get_line_total(self) -> float:
        """Calculate total for this line"""
        return self.cart_item.get_line_total()


@dataclass
class Prescription(Aggregate):
    """
    Aggregate Root: Prescription
    Manages prescription lifecycle from creation through fulfillment
    
    Responsibilities:
    - Track prescription items (drugs with dosages)
    - Validate prescription against drug requirements
    - Track prescription and cart status
    - Calculate totals
    - Manage prescription validity
    - Raise domain events
    """
    prescription_id: PrescriptionId = None
    customer_id: CustomerId = None
    
    # Core data
    prescriber_info: PrescriberInfo = None
    diagnoses: List[Diagnosis] = field(default_factory=list)
    validity: PrescriptionValidity = None
    line_items: List[PrescriptionLineItem] = field(default_factory=list)
    
    # Status tracking
    prescription_status: PrescriptionStatus = PrescriptionStatus.DRAFT
    cart_status: CartStatus = CartStatus.ACTIVE
    
    # Financial
    subtotal: Money = None
    total_amount: Money = None
    
    # Dates
    created_at: datetime = field(default_factory=datetime.now)
    submitted_date: Optional[datetime] = None
    confirmed_date: Optional[datetime] = None
    fulfilled_date: Optional[datetime] = None
    
    # Additional
    notes: str = ""
    _events: List = field(default_factory=list)
    
    def __post_init__(self):
        if self.subtotal is None:
            self.subtotal = Money(0, "VND")
        if self.total_amount is None:
            self.total_amount = Money(0, "VND")
    
    def add_item(self, cart_item: CartItem, drug_requirement: DrugRequirement) -> None:
        """Add drug item to prescription"""
        if self.prescription_status == PrescriptionStatus.SUBMITTED:
            raise ValueError("Cannot add items to submitted prescription")
        if self.prescription_status == PrescriptionStatus.FULFILLED:
            raise ValueError("Cannot add items to fulfilled prescription")
        if self.prescription_status == PrescriptionStatus.CANCELLED:
            raise ValueError("Cannot add items to cancelled prescription")
        
        # Validate drug requirement fits prescription
        if drug_requirement and not self._validate_drug_requirement(cart_item, drug_requirement):
            self.add_event(PrescriptionRequirementValidated(
                aggregate_id=str(self.prescription_id),
                prescription_id=str(self.prescription_id),
                product_id=str(cart_item.product_id),
                sku=cart_item.sku,
                validation_result="INVALID",
                warnings="Drug requirement validation failed",
            ))
            raise ValueError("Drug requirement validation failed")
        
        # Check not already in prescription
        for item in self.line_items:
            if item.cart_item.product_id == cart_item.product_id:
                raise ValueError("Product already in prescription")
        
        # Add item
        line_item = PrescriptionLineItem(
            cart_item=cart_item,
            drug_requirement=drug_requirement
        )
        self.line_items.append(line_item)
        
        # Update total
        self._recalculate_total()
        
        # Raise event
        self.add_event(PrescriptionItemAdded(
            aggregate_id=str(self.prescription_id),
            prescription_id=str(self.prescription_id),
            product_id=str(cart_item.product_id),
            sku=cart_item.sku,
            product_name=cart_item.product_name,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            currency=cart_item.currency,
        ))
    
    def remove_item(self, product_id: ProductId) -> None:
        """Remove item from prescription"""
        if self.prescription_status == PrescriptionStatus.SUBMITTED:
            raise ValueError("Cannot remove items from submitted prescription")
        
        for i, item in enumerate(self.line_items):
            if item.cart_item.product_id == product_id:
                removed_item = self.line_items.pop(i)
                
                # Recalculate
                self._recalculate_total()
                
                # Raise event
                self.add_event(PrescriptionItemRemoved(
                    aggregate_id=str(self.prescription_id),
                    prescription_id=str(self.prescription_id),
                    product_id=str(product_id),
                    sku=removed_item.cart_item.sku,
                    quantity_removed=removed_item.cart_item.quantity,
                ))
                return
        
        raise ValueError(f"Product {product_id} not in prescription")
    
    def update_item_quantity(self, product_id: ProductId, new_quantity: int) -> None:
        """Update quantity for item"""
        if new_quantity <= 0:
            raise ValueError("New quantity must be positive")
        
        for item in self.line_items:
            if item.cart_item.product_id == product_id:
                old_qty = item.cart_item.quantity
                
                # Create new cart item with updated quantity
                new_cart_item = CartItem(
                    product_id=item.cart_item.product_id,
                    sku=item.cart_item.sku,
                    product_name=item.cart_item.product_name,
                    quantity=new_quantity,
                    unit=item.cart_item.unit,
                    unit_price=item.cart_item.unit_price,
                    currency=item.cart_item.currency,
                    requires_prescription=item.cart_item.requires_prescription,
                )
                
                item.cart_item = new_cart_item
                self._recalculate_total()
                
                self.add_event(PrescriptionItemQuantityChanged(
                    aggregate_id=str(self.prescription_id),
                    prescription_id=str(self.prescription_id),
                    product_id=str(product_id),
                    old_quantity=old_qty,
                    new_quantity=new_quantity,
                ))
                return
        
        raise ValueError(f"Product {product_id} not in prescription")
    
    def submit_prescription(self) -> None:
        """Submit prescription for dispensing"""
        if self.prescription_status != PrescriptionStatus.DRAFT:
            raise ValueError(f"Cannot submit prescription in {self.prescription_status.value} status")
        
        if not self.line_items:
            raise ValueError("Cannot submit empty prescription")
        
        if not self.validity.is_valid():
            self.add_event(PrescriptionValidationFailed(
                aggregate_id=str(self.prescription_id),
                prescription_id=str(self.prescription_id),
                customer_id=str(self.customer_id),
                failure_reason="Prescription has expired or not yet valid",
            ))
            raise ValueError("Prescription not valid")
        
        self.prescription_status = PrescriptionStatus.SUBMITTED
        self.cart_status = CartStatus.SUBMITTED
        self.submitted_date = datetime.now()
        
        self.add_event(PrescriptionSubmitted(
            aggregate_id=str(self.prescription_id),
            prescription_id=str(self.prescription_id),
            customer_id=str(self.customer_id),
            total_amount=self.total_amount.amount,
            currency=self.total_amount.currency,
            items_count=len(self.line_items),
        ))
    
    def confirm_prescription(self) -> None:
        """Pharmacy confirms prescription"""
        if self.prescription_status != PrescriptionStatus.SUBMITTED:
            raise ValueError(f"Cannot confirm prescription in {self.prescription_status.value} status")
        
        self.prescription_status = PrescriptionStatus.CONFIRMED
        self.confirmed_date = datetime.now()
        
        self.add_event(PrescriptionConfirmed(
            aggregate_id=str(self.prescription_id),
            prescription_id=str(self.prescription_id),
            customer_id=str(self.customer_id),
        ))
    
    def fulfill_item(self, product_id: ProductId, quantity: int) -> None:
        """Mark item quantity as fulfilled"""
        if self.prescription_status not in [PrescriptionStatus.CONFIRMED, PrescriptionStatus.FULFILLED]:
            raise ValueError(f"Cannot fulfill in {self.prescription_status.value} status")
        
        for item in self.line_items:
            if item.cart_item.product_id == product_id:
                item.fulfill(quantity)
                
                # Check if fully fulfilled
                if all(i.is_fully_fulfilled() for i in self.line_items):
                    self.prescription_status = PrescriptionStatus.FULFILLED
                    self.fulfilled_date = datetime.now()
                    
                    self.add_event(PrescriptionFulfilled(
                        aggregate_id=str(self.prescription_id),
                        prescription_id=str(self.prescription_id),
                        customer_id=str(self.customer_id),
                        total_items=len(self.line_items),
                    ))
                
                return
        
        raise ValueError(f"Product {product_id} not in prescription")
    
    def cancel_prescription(self, reason: str = "") -> None:
        """Cancel prescription"""
        if self.prescription_status in [PrescriptionStatus.FULFILLED, PrescriptionStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel {self.prescription_status.value} prescription")
        
        self.prescription_status = PrescriptionStatus.CANCELLED
        self.cart_status = CartStatus.ABANDONED
        
        self.add_event(PrescriptionCancelled(
            aggregate_id=str(self.prescription_id),
            prescription_id=str(self.prescription_id),
            customer_id=str(self.customer_id),
            cancellation_reason=reason,
        ))
    
    def clear_cart(self) -> None:
        """Clear all items from cart"""
        items_count = len(self.line_items)
        self.line_items.clear()
        self._recalculate_total()
        
        self.add_event(CartCleared(
            aggregate_id=str(self.prescription_id),
            prescription_id=str(self.prescription_id),
            items_count=items_count,
        ))
    
    def _recalculate_total(self) -> None:
        """Recalculate prescription total"""
        if not self.line_items:
            self.subtotal = Money(0, "VND")
            self.total_amount = Money(0, "VND")
            return
        
        total = Money(0, self.line_items[0].cart_item.currency)
        for item in self.line_items:
            item_total = Money(item.get_line_total(), item.cart_item.currency)
            total = total.add(item_total)
        
        self.subtotal = total
        self.total_amount = total
        
        self.add_event(CartTotalCalculated(
            aggregate_id=str(self.prescription_id),
            prescription_id=str(self.prescription_id),
            total_amount=total.amount,
            currency=total.currency,
            items_count=len(self.line_items),
        ))
    
    def _validate_drug_requirement(self, cart_item: CartItem, requirement: DrugRequirement) -> bool:
        """Validate drug requirement"""
        # Basic validation - can be expanded with business rules
        if not requirement.frequency or not requirement.duration or not requirement.dosage:
            return False
        return True
    
    def get_unfulfilled_items(self) -> List[PrescriptionLineItem]:
        """Get items not yet fulfilled"""
        return [item for item in self.line_items if not item.is_fully_fulfilled()]
    
    def is_partially_fulfilled(self) -> bool:
        """Check if some but not all items fulfilled"""
        return any(item.fulfilled_quantity > 0 for item in self.line_items) and \
               not all(item.is_fully_fulfilled() for item in self.line_items)
    
    def check_validity(self) -> bool:
        """Check if prescription is still valid"""
        if not self.validity:
            return False
        return self.validity.is_valid()
