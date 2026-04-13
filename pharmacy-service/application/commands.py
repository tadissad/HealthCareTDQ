"""
Pharmacy Application Layer - Commands

Commands represent requests to modify product state
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class CreateProductCommand:
    """Command: Create new product"""
    sku: str
    generic_name: str
    trade_name: str
    dosage_form: str                  # tablet, capsule, injectable, etc.
    dosage_strength: str              # 500mg, 250mg/5ml, etc.
    manufacturer_name: str
    manufacturer_country: str
    price: float
    atc_code: str
    icd_codes: List[str]
    requires_prescription: bool
    category: str
    description: Optional[str] = None
    manufacturer_reg_code: Optional[str] = None


@dataclass
class ReceiveInventoryCommand:
    """Command: Receive new inventory batch"""
    product_id: str
    batch_number: str
    quantity: int
    expiry_date: datetime


@dataclass
class SellProductCommand:
    """Command: Decrease stock from sale"""
    product_id: str
    quantity: int


@dataclass
class ScrapProductCommand:
    """Command: Remove damaged/expired product"""
    product_id: str
    quantity: int


@dataclass
class ChangePriceCommand:
    """Command: Change product price"""
    product_id: str
    new_price: float
    changed_by: str


@dataclass
class AdjustMinStockCommand:
    """Command: Adjust minimum stock level"""
    product_id: str
    min_level: int


@dataclass
class ChangeManufacturerCommand:
    """Command: Change product manufacturer"""
    product_id: str
    new_manufacturer_name: str
    new_manufacturer_country: str
    new_reg_code: Optional[str] = None


@dataclass
class CheckExpiringProductsCommand:
    """Command: Check all products for expiring batches"""
    days_threshold: int = 90


@dataclass
class DeactivateProductCommand:
    """Command: Deactivate product (stop selling)"""
    product_id: str
    reason: str
