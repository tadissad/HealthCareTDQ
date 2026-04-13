"""
Pharmacy Application Layer - Command Handlers
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from .commands import (
    CreateProductCommand, ReceiveInventoryCommand, SellProductCommand,
    ScrapProductCommand, ChangePriceCommand, AdjustMinStockCommand,
    ChangeManufacturerCommand, CheckExpiringProductsCommand,
    DeactivateProductCommand
)
from ..domain import (
    ProductId, ProductCreationService, InventoryManagementService,
    PricingService, QualityControlService, ManufacturerInfo, IProductRepository
)


class CreateProductCommandHandler:
    """Handle: CreateProductCommand"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
        self.creation_service = ProductCreationService(product_repo)
    
    def handle(self, command: CreateProductCommand) -> dict:
        try:
            product = self.creation_service.create_product(
                sku_str=command.sku,
                generic_name=command.generic_name,
                trade_name=command.trade_name,
                dosage_form_str=command.dosage_form,
                dosage_strength_str=command.dosage_strength,
                manufacturer_name=command.manufacturer_name,
                manufacturer_country=command.manufacturer_country,
                price_amount=command.price,
                atc_code_str=command.atc_code,
                icd_codes=command.icd_codes,
                requires_prescription=command.requires_prescription,
                category=command.category,
                description=command.description,
                manufacturer_reg_code=command.manufacturer_reg_code,
            )
            
            return {
                "success": True,
                "product_id": str(product.id),
                "message": "Product created successfully",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ReceiveInventoryCommandHandler:
    """Handle: ReceiveInventoryCommand"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
        self.inventory_service = InventoryManagementService(product_repo)
    
    def handle(self, command: ReceiveInventoryCommand) -> dict:
        try:
            product_id = ProductId(command.product_id)
            self.inventory_service.receive_inventory(
                product_id=product_id,
                batch_number_str=command.batch_number,
                quantity=command.quantity,
                expiry_date_obj=command.expiry_date,
            )
            
            return {
                "success": True,
                "message": f"Received {command.quantity} units",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class SellProductCommandHandler:
    """Handle: SellProductCommand"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
        self.inventory_service = InventoryManagementService(product_repo)
    
    def handle(self, command: SellProductCommand) -> dict:
        try:
            product_id = ProductId(command.product_id)
            self.inventory_service.sell_product(
                product_id=product_id,
                quantity=command.quantity,
            )
            
            return {
                "success": True,
                "message": f"Sold {command.quantity} units",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ScrapProductCommandHandler:
    """Handle: ScrapProductCommand"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
        self.inventory_service = InventoryManagementService(product_repo)
    
    def handle(self, command: ScrapProductCommand) -> dict:
        try:
            product_id = ProductId(command.product_id)
            self.inventory_service.scrap_product(
                product_id=product_id,
                quantity=command.quantity,
            )
            
            return {
                "success": True,
                "message": f"Scrapped {command.quantity} units",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ChangePriceCommandHandler:
    """Handle: ChangePriceCommand"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
        self.pricing_service = PricingService(product_repo)
    
    def handle(self, command: ChangePriceCommand) -> dict:
        try:
            product_id = ProductId(command.product_id)
            self.pricing_service.change_price(
                product_id=product_id,
                new_price=command.new_price,
                changed_by=command.changed_by,
            )
            
            return {
                "success": True,
                "message": f"Price changed to {command.new_price}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class AdjustMinStockCommandHandler:
    """Handle: AdjustMinStockCommand"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
        self.quality_service = QualityControlService(product_repo)
    
    def handle(self, command: AdjustMinStockCommand) -> dict:
        try:
            product_id = ProductId(command.product_id)
            self.quality_service.adjust_minimum_stock(
                product_id=product_id,
                min_level=command.min_level,
            )
            
            return {
                "success": True,
                "message": f"Minimum stock set to {command.min_level}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ChangeManufacturerCommandHandler:
    """Handle: ChangeManufacturerCommand"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, command: ChangeManufacturerCommand) -> dict:
        try:
            product_id = ProductId(command.product_id)
            product = self.product_repo.get_by_id(product_id)
            
            if not product:
                return {"success": False, "error": "Product not found"}
            
            new_manufacturer = ManufacturerInfo(
                name=command.new_manufacturer_name,
                country=command.new_manufacturer_country,
                registration_code=command.new_reg_code,
            )
            
            product.change_manufacturer(new_manufacturer)
            self.product_repo.update(product)
            
            return {
                "success": True,
                "message": "Manufacturer updated",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class CheckExpiringProductsCommandHandler:
    """Handle: CheckExpiringProductsCommand"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
        self.quality_service = QualityControlService(product_repo)
    
    def handle(self, command: CheckExpiringProductsCommand) -> dict:
        try:
            expiring = self.quality_service.check_expiring_products(
                days_threshold=command.days_threshold
            )
            
            return {
                "success": True,
                "expiring_products_count": len(expiring),
                "message": f"Found {len(expiring)} products with expiring batches",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class DeactivateProductCommandHandler:
    """Handle: DeactivateProductCommand"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, command: DeactivateProductCommand) -> dict:
        try:
            product_id = ProductId(command.product_id)
            product = self.product_repo.get_by_id(product_id)
            
            if not product:
                return {"success": False, "error": "Product not found"}
            
            product.deactivate()
            self.product_repo.update(product)
            
            return {
                "success": True,
                "message": "Product deactivated",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
