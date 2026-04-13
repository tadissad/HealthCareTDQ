"""
Pharmacy Infrastructure Layer - Repository Implementation
Implements IProductRepository with ORM model persistence
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from .models import ProductModel, BatchModel, InventoryLocationModel
from ...domain import (
    Product, Batch, InventoryLocation,
    ProductId, SKU, Price, Quantity, ExpiryDate, BatchNumber,
    DosageStrength, DosageForm, ManufacturerInfo,
    ATCCode, ICDCode, PrescriptionRequirement,
    IProductRepository
)


class ProductRepositoryImpl(IProductRepository):
    """
    Implementation of IProductRepository using Django ORM
    Handles mapping between domain entities and ORM models
    """
    
    def _model_to_entity(self, model: ProductModel) -> Product:
        """Transform ProductModel ORM to Product domain entity"""
        
        # Load batches
        batch_models = BatchModel.objects.filter(product=model)
        batches = []
        for batch_model in batch_models:
            batch = Batch(
                batch_number=BatchNumber(batch_model.batch_number),
                received_date=batch_model.received_date,
                quantity=Quantity(
                    value=batch_model.quantity_value,
                    unit=batch_model.quantity_unit
                ),
                expiry_date=ExpiryDate(batch_model.expiry_date)
            )
            batches.append(batch)
        
        # Reconstruct entity
        product = Product(
            product_id=ProductId(model.product_id),
            sku=SKU(model.sku),
            generic_name=model.generic_name,
            trade_name=model.trade_name,
            dosage_form=DosageForm(model.dosage_form),
            dosage_strength=DosageStrength(model.dosage_strength),
            manufacturer=ManufacturerInfo(
                name=model.manufacturer_name,
                country=model.manufacturer_country
            ),
            price=Price(
                amount=float(model.price_amount),
                currency=model.price_currency
            ),
            atc_code=ATCCode(model.atc_code),
            icd_codes=[ICDCode(code) for code in model.icd_codes],
            category=model.category,
            prescription_requirement=PrescriptionRequirement(
                requires_prescription=model.requires_prescription
            ),
            description=model.description,
            batches=batches,
            total_quantity=Quantity(
                value=model.total_quantity_value,
                unit=model.total_quantity_unit
            ),
            min_stock_level=Quantity(
                value=model.min_stock_level_value,
                unit=model.total_quantity_unit
            ),
            reorder_point=Quantity(
                value=model.reorder_point_value,
                unit=model.total_quantity_unit
            ),
            active=model.active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        
        return product
    
    def _entity_to_model(self, product: Product) -> ProductModel:
        """Transform Product domain entity to ProductModel ORM"""
        
        model = ProductModel(
            product_id=str(product.id),
            sku=str(product.sku),
            generic_name=product.generic_name,
            trade_name=product.trade_name,
            dosage_form=str(product.dosage_form),
            dosage_strength=str(product.dosage_strength),
            manufacturer_name=product.manufacturer.name,
            manufacturer_country=product.manufacturer.country,
            price_amount=product.price.amount,
            price_currency=product.price.currency,
            atc_code=str(product.atc_code),
            icd_codes=[str(code) for code in product.icd_codes],
            category=product.category,
            requires_prescription=product.prescription_requirement.requires_prescription,
            description=product.description,
            total_quantity_value=product.total_quantity.value,
            total_quantity_unit=product.total_quantity.unit,
            min_stock_level_value=product.min_stock_level.value,
            reorder_point_value=product.reorder_point.value,
            active=product.active,
        )
        if product.created_at:
            model.created_at = product.created_at
        if product.updated_at:
            model.updated_at = product.updated_at
        
        return model
    
    def add(self, product: Product) -> None:
        """Persist new product to database"""
        
        # Save product model
        model = self._entity_to_model(product)
        model.save()
        
        # Save batches
        for batch in product.batches:
            batch_model = BatchModel(
                batch_id=str(uuid4()),
                product_id=str(product.id),
                batch_number=str(batch.batch_number),
                received_date=batch.received_date,
                quantity_value=batch.quantity.value,
                quantity_unit=batch.quantity.unit,
                expiry_date=batch.expiry_date.value
            )
            batch_model.save()
    
    def update(self, product: Product) -> None:
        """Update existing product in database"""
        
        try:
            model = ProductModel.objects.get(product_id=str(product.id))
        except ProductModel.DoesNotExist:
            raise Exception(f"Product {product.id} not found")
        
        # Update model fields
        model.sku = str(product.sku)
        model.generic_name = product.generic_name
        model.trade_name = product.trade_name
        model.dosage_form = str(product.dosage_form)
        model.dosage_strength = str(product.dosage_strength)
        model.manufacturer_name = product.manufacturer.name
        model.manufacturer_country = product.manufacturer.country
        model.price_amount = product.price.amount
        model.price_currency = product.price.currency
        model.atc_code = str(product.atc_code)
        model.icd_codes = [str(code) for code in product.icd_codes]
        model.category = product.category
        model.requires_prescription = product.prescription_requirement.requires_prescription
        model.description = product.description
        model.total_quantity_value = product.total_quantity.value
        model.total_quantity_unit = product.total_quantity.unit
        model.min_stock_level_value = product.min_stock_level.value
        model.reorder_point_value = product.reorder_point.value
        model.active = product.active
        model.updated_at = datetime.now()
        model.save()
        
        # Update batches
        BatchModel.objects.filter(product_id=str(product.id)).delete()
        for batch in product.batches:
            batch_model = BatchModel(
                batch_id=str(uuid4()),
                product_id=str(product.id),
                batch_number=str(batch.batch_number),
                received_date=batch.received_date,
                quantity_value=batch.quantity.value,
                quantity_unit=batch.quantity.unit,
                expiry_date=batch.expiry_date.value
            )
            batch_model.save()
    
    def remove(self, product_id: ProductId) -> None:
        """Delete product from database"""
        try:
            model = ProductModel.objects.get(product_id=str(product_id))
            model.delete()
        except ProductModel.DoesNotExist:
            pass
    
    def get_by_id(self, product_id: ProductId) -> Optional[Product]:
        """Retrieve product by ID"""
        try:
            model = ProductModel.objects.get(product_id=str(product_id))
            return self._model_to_entity(model)
        except ProductModel.DoesNotExist:
            return None
    
    def get_by_sku(self, sku: SKU) -> Optional[Product]:
        """Retrieve product by SKU"""
        try:
            model = ProductModel.objects.get(sku=str(sku))
            return self._model_to_entity(model)
        except ProductModel.DoesNotExist:
            return None
    
    def get_by_atc_code(self, atc_code: ATCCode) -> List[Product]:
        """Retrieve all products with given ATC code"""
        models = ProductModel.objects.filter(atc_code=str(atc_code))
        return [self._model_to_entity(m) for m in models]
    
    def list_all(self) -> List[Product]:
        """Retrieve all products"""
        models = ProductModel.objects.all()
        return [self._model_to_entity(m) for m in models]
    
    def list_active(self) -> List[Product]:
        """Retrieve all active products"""
        models = ProductModel.objects.filter(active=True)
        return [self._model_to_entity(m) for m in models]
    
    def list_low_stock(self, threshold: int = None) -> List[Product]:
        """Retrieve products with stock below threshold or reorder point"""
        all_products = self.list_all()
        low_stock = []
        
        for product in all_products:
            check_level = threshold if threshold else product.reorder_point.value
            if product.total_quantity.value < check_level:
                low_stock.append(product)
        
        return low_stock
    
    def search_by_name(self, search_term: str) -> List[Product]:
        """Search products by generic or trade name"""
        models = ProductModel.objects.filter(
            generic_name__icontains=search_term
        ) | ProductModel.objects.filter(
            trade_name__icontains=search_term
        )
        return [self._model_to_entity(m) for m in models]
    
    def search_by_category(self, category: str) -> List[Product]:
        """Retrieve products by category"""
        models = ProductModel.objects.filter(category=category)
        return [self._model_to_entity(m) for m in models]
