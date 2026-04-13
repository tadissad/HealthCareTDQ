"""
Pharmacy Domain - Entities and Aggregates

Product là Aggregate Root của pharmacy service
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared_ddd.base import Aggregate, Entity
from .value_objects import (
    ProductId, SKU, Price, Quantity, ExpiryDate, BatchNumber, DosageStrength,
    DosageForm, ManufacturerInfo, ATCCode, ICDCode, PrescriptionRequirement
)
from .events import (
    ProductAdded, ProductPriceChanged, InventoryAdjusted, LowStockAlert,
    ProductExpiring, ProductExpired, ManufacturerChanged, BatchAdded
)


class Batch(Entity):
    """Batch/Lot entity - tracks inventory by batch including expiry"""
    
    def __init__(
        self,
        id: str,
        product_id: ProductId,
        batch_number: BatchNumber,
        quantity: Quantity,
        expiry_date: ExpiryDate,
        received_date: datetime,
    ):
        super().__init__(id)
        self.product_id = product_id
        self.batch_number = batch_number
        self.quantity = quantity
        self.expiry_date = expiry_date
        self.received_date = received_date
    
    def is_expired(self) -> bool:
        """Check if batch is expired"""
        return self.expiry_date.is_expired()
    
    def days_until_expiry(self) -> int:
        """Days until this batch expires"""
        return self.expiry_date.days_until_expiry()
    
    def remove_stock(self, qty: int) -> "Batch":
        """Remove stock from batch"""
        self.quantity = self.quantity.subtract(qty)
        return self


class InventoryLocation(Entity):
    """Where inventory is physically stored"""
    
    def __init__(
        self,
        id: str,
        warehouse: str,
        shelf: str,
        row: str,
        position: str,
    ):
        super().__init__(id)
        self.warehouse = warehouse
        self.shelf = shelf
        self.row = row
        self.position = position
    
    def get_location_code(self) -> str:
        """Full location code"""
        return f"{self.warehouse}-{self.shelf}-{self.row}-{self.position}"


class Product(Aggregate):
    """
    Product Aggregate Root
    
    Represents a pharmaceutical product or medical device.
    Contains all information about the product and derives variants (batches).
    """
    
    def __init__(
        self,
        id: ProductId,
        sku: SKU,
        generic_name: str,
        trade_name: str,
        dosage_form: DosageForm,
        dosage_strength: DosageStrength,
        manufacturer: ManufacturerInfo,
        price: Price,
        atc_code: ATCCode,
        icd_codes: List[ICDCode],
        prescription_requirement: PrescriptionRequirement,
        category: str,
        description: Optional[str] = None,
    ):
        super().__init__(id)
        
        # Product Identity
        self.sku = sku
        
        # Product Names
        self.generic_name = generic_name
        self.trade_name = trade_name
        
        # Dosage Information
        self.dosage_form = dosage_form
        self.dosage_strength = dosage_strength
        
        # Manufacturing
        self.manufacturer = manufacturer
        
        # Pricing
        self.price = price
        
        # Classification
        self.atc_code = atc_code
        self.icd_codes = icd_codes
        self.category = category
        
        # Regulations
        self.prescription_requirement = prescription_requirement
        
        # Description
        self.description = description
        
        # Inventory tracking
        self.batches: List[Batch] = []
        self.total_quantity = Quantity(0)
        
        # Stock levels
        self.min_stock_level = Quantity(10)  # Default minimum
        self.reorder_point = Quantity(20)
        
        # Metadata
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.active = True
        
        # Raise event
        self.add_event(
            ProductAdded(
                aggregate_id=str(id),
                product_id=str(id),
                sku=str(sku),
                name=trade_name,
                manufacturer=manufacturer.name,
                occurred_at=self.created_at,
            )
        )
    
    def change_price(self, new_price: Price, changed_by: str) -> None:
        """Change product price"""
        if new_price == self.price:
            return
        
        old_price = self.price.amount
        self.price = new_price
        self.updated_at = datetime.now()
        
        self.add_event(
            ProductPriceChanged(
                aggregate_id=str(self.id),
                product_id=str(self.id),
                old_price=old_price,
                new_price=new_price.amount,
                changed_by=changed_by,
                occurred_at=self.updated_at,
            )
        )
    
    def receive_batch(
        self,
        batch_id: str,
        batch_number: BatchNumber,
        quantity: Quantity,
        expiry_date: ExpiryDate,
    ) -> None:
        """Receive new batch of product"""
        batch = Batch(
            id=batch_id,
            product_id=self.id,
            batch_number=batch_number,
            quantity=quantity,
            expiry_date=expiry_date,
            received_date=datetime.now(),
        )
        
        self.batches.append(batch)
        self.total_quantity = self.total_quantity.add(quantity.value)
        self.updated_at = datetime.now()
        
        self.add_event(
            BatchAdded(
                aggregate_id=str(self.id),
                product_id=str(self.id),
                batch_number=str(batch_number),
                quantity_received=quantity.value,
                expiry_date=expiry_date.value,
                occurred_at=self.updated_at,
            )
        )
    
    def remove_stock(self, quantity: int, reason: str) -> None:
        """
        Remove stock from inventory
        Removes from oldest batch first (FIFO)
        """
        if quantity > self.total_quantity.value:
            raise ValueError(f"Not enough stock. Has: {self.total_quantity.value}, Need: {quantity}")
        
        remaining = quantity
        for batch in self.batches:
            if remaining <= 0:
                break
            if batch.quantity.value > 0:
                to_remove = min(remaining, batch.quantity.value)
                batch.remove_stock(to_remove)
                remaining -= to_remove
        
        old_qty = self.total_quantity.value
        self.total_quantity = self.total_quantity.subtract(quantity)
        self.updated_at = datetime.now()
        
        self.add_event(
            InventoryAdjusted(
                aggregate_id=str(self.id),
                product_id=str(self.id),
                old_quantity=old_qty,
                new_quantity=self.total_quantity.value,
                reason=reason,
                occurred_at=self.updated_at,
            )
        )
        
        # Check if low stock
        self._check_low_stock()
    
    def adjust_min_stock_level(self, new_level: Quantity) -> None:
        """Update minimum stock level"""
        self.min_stock_level = new_level
        self.updated_at = datetime.now()
        self._check_low_stock()
    
    def _check_low_stock(self) -> None:
        """Check and raise event if stock is low"""
        if self.total_quantity.is_low_stock(self.min_stock_level.value):
            self.add_event(
                LowStockAlert(
                    aggregate_id=str(self.id),
                    product_id=str(self.id),
                    current_quantity=self.total_quantity.value,
                    threshold=self.min_stock_level.value,
                    sku=str(self.sku),
                    occurred_at=datetime.now(),
                )
            )
    
    def check_expiring_batches(self, days_threshold: int = 90) -> None:
        """Check for batches expiring soon and raise events"""
        threshold_date = datetime.now() + timedelta(days=days_threshold)
        
        for batch in self.batches:
            if batch.expiry_date.is_expired():
                # Already expired
                if batch.quantity.value > 0:
                    self.add_event(
                        ProductExpired(
                            aggregate_id=str(self.id),
                            product_id=str(self.id),
                            batch_number=str(batch.batch_number),
                            quantity_expired=batch.quantity.value,
                            occurred_at=datetime.now(),
                        )
                    )
            elif batch.expiry_date.value <= threshold_date:
                # Expiring soon
                self.add_event(
                    ProductExpiring(
                        aggregate_id=str(self.id),
                        product_id=str(self.id),
                        batch_number=str(batch.batch_number),
                        expiry_date=batch.expiry_date.value,
                        days_until_expiry=batch.days_until_expiry(),
                        quantity_expiring=batch.quantity.value,
                        occurred_at=datetime.now(),
                    )
                )
    
    def change_manufacturer(self, new_manufacturer: ManufacturerInfo) -> None:
        """Change manufacturer"""
        old_manufacturer = self.manufacturer.name
        self.manufacturer = new_manufacturer
        self.updated_at = datetime.now()
        
        self.add_event(
            ManufacturerChanged(
                aggregate_id=str(self.id),
                product_id=str(self.id),
                old_manufacturer=old_manufacturer,
                new_manufacturer=new_manufacturer.name,
                occurred_at=self.updated_at,
            )
        )
    
    def deactivate(self) -> None:
        """Deactivate product (stop selling)"""
        self.active = False
        self.updated_at = datetime.now()
    
    def get_total_value(self) -> float:
        """Calculate total inventory value"""
        return self.total_quantity.value * self.price.amount
    
    def get_expiring_soon(self, days: int = 30) -> List[Batch]:
        """Get batches expiring within X days"""
        threshold = datetime.now() + timedelta(days=days)
        return [b for b in self.batches if b.expiry_date.value <= threshold and not b.is_expired()]
