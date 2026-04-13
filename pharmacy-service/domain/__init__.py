"""
Pharmacy Domain Package

Contains all domain logic for pharmacy bounded context
"""

from .entities import Product, Batch, InventoryLocation
from .value_objects import (
    ProductId, SKU, Price, Quantity, ExpiryDate, BatchNumber, DosageStrength,
    DosageForm, ManufacturerInfo, ATCCode, ICDCode, PrescriptionRequirement
)
from .events import (
    ProductAdded, ProductPriceChanged, InventoryAdjusted, LowStockAlert,
    ProductExpiring, ProductExpired, ManufacturerChanged, BatchAdded
)
from .repositories import IProductRepository
from .domain_services import (
    ProductCreationService, InventoryManagementService, PricingService,
    QualityControlService
)

__all__ = [
    # Entities
    "Product", "Batch", "InventoryLocation",
    # Value Objects
    "ProductId", "SKU", "Price", "Quantity", "ExpiryDate", "BatchNumber",
    "DosageStrength", "DosageForm", "ManufacturerInfo", "ATCCode", "ICDCode",
    "PrescriptionRequirement",
    # Events
    "ProductAdded", "ProductPriceChanged", "InventoryAdjusted", "LowStockAlert",
    "ProductExpiring", "ProductExpired", "ManufacturerChanged", "BatchAdded",
    # Repository
    "IProductRepository",
    # Services
    "ProductCreationService", "InventoryManagementService", "PricingService",
    "QualityControlService",
]
