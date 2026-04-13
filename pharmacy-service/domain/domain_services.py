"""
Pharmacy Domain Services

Contains complex business logic for product management and inventory
"""

from datetime import datetime, timedelta
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared_ddd.base import DomainService
from .entities import Product
from .value_objects import (
    ProductId, SKU, Price, Quantity, ExpiryDate, BatchNumber, DosageStrength,
    DosageForm, ManufacturerInfo, ATCCode, ICDCode, PrescriptionRequirement
)
from .repositories import IProductRepository


class ProductCreationService(DomainService):
    """Domain Service for creating new products"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def execute(self, *args, **kwargs):
        pass
    
    def create_product(
        self,
        sku_str: str,
        generic_name: str,
        trade_name: str,
        dosage_form_str: str,
        dosage_strength_str: str,
        manufacturer_name: str,
        manufacturer_country: str,
        price_amount: float,
        atc_code_str: str,
        icd_codes: list,
        requires_prescription: bool,
        category: str,
        description: Optional[str] = None,
        manufacturer_reg_code: Optional[str] = None,
    ) -> Product:
        """Create a new product"""
        
        # Create value objects
        product_id = ProductId(f"PROD_{SKU(sku_str).value}_{int(datetime.now().timestamp()*1000)}")
        sku = SKU(sku_str)
        dosage_form = DosageForm(dosage_form_str)
        dosage_strength = DosageStrength(dosage_strength_str)
        manufacturer = ManufacturerInfo(manufacturer_name, manufacturer_country, manufacturer_reg_code)
        price = Price(price_amount)
        atc_code = ATCCode(atc_code_str)
        
        icd_list = [ICDCode(code) for code in icd_codes]
        prescription_req = PrescriptionRequirement(requires_prescription)
        
        # Create aggregate
        product = Product(
            id=product_id,
            sku=sku,
            generic_name=generic_name,
            trade_name=trade_name,
            dosage_form=dosage_form,
            dosage_strength=dosage_strength,
            manufacturer=manufacturer,
            price=price,
            atc_code=atc_code,
            icd_codes=icd_list,
            prescription_requirement=prescription_req,
            category=category,
            description=description,
        )
        
        # Persist
        self.product_repo.add(product)
        
        return product


class InventoryManagementService(DomainService):
    """Domain Service for inventory operations"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def execute(self, *args, **kwargs):
        pass
    
    def receive_inventory(
        self,
        product_id: ProductId,
        batch_number_str: str,
        quantity: int,
        expiry_date_obj: datetime,
    ) -> None:
        """Receive new inventory batch"""
        
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        batch_number = BatchNumber(batch_number_str)
        quantity_obj = Quantity(quantity)
        expiry_date = ExpiryDate(expiry_date_obj)
        
        # Generate batch ID
        batch_id = f"BATCH_{batch_number_str}_{int(datetime.now().timestamp()*1000)}"
        
        product.receive_batch(batch_id, batch_number, quantity_obj, expiry_date)
        self.product_repo.update(product)
    
    def sell_product(
        self,
        product_id: ProductId,
        quantity: int,
    ) -> None:
        """Remove product from stock (sale)"""
        
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        product.remove_stock(quantity, reason="sold")
        self.product_repo.update(product)
    
    def scrap_product(
        self,
        product_id: ProductId,
        quantity: int,
    ) -> None:
        """Remove damaged/expired product from stock"""
        
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        product.remove_stock(quantity, reason="damaged")
        self.product_repo.update(product)


class PricingService(DomainService):
    """Domain Service for pricing operations"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def execute(self, *args, **kwargs):
        pass
    
    def change_price(
        self,
        product_id: ProductId,
        new_price: float,
        changed_by: str,
    ) -> None:
        """Change product price"""
        
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        new_price_obj = Price(new_price)
        product.change_price(new_price_obj, changed_by)
        self.product_repo.update(product)


class QualityControlService(DomainService):
    """Domain Service for quality control and expiry management"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def execute(self, *args, **kwargs):
        pass
    
    def check_expiring_products(self, days_threshold: int = 90) -> list:
        """Check all products for expiring batches"""
        
        all_products = self.product_repo.list_all()
        expiring_products = []
        
        for product in all_products:
            product.check_expiring_batches(days_threshold)
            if product.get_events():  # If any events raised
                expiring_products.append(product)
                self.product_repo.update(product)
        
        return expiring_products
    
    def adjust_minimum_stock(
        self,
        product_id: ProductId,
        min_level: int,
    ) -> None:
        """Adjust minimum stock level warning"""
        
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        quantity = Quantity(min_level)
        product.adjust_min_stock_level(quantity)
        self.product_repo.update(product)
