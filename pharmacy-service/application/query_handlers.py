"""
Pharmacy Application Layer - Query Handlers
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from .queries import (
    GetProductByIdQuery, GetProductBySKUQuery, GetProductByATCQuery,
    ListAllProductsQuery, ListActiveProductsQuery, ListLowStockProductsQuery,
    SearchProductsQuery, GetProductsByCategoryQuery, GetProductInventoryQuery,
    GetExpiringProductsQuery
)
from ..domain import ProductId, SKU, ATCCode, IProductRepository


def _product_to_dto(product) -> dict:
    """Transform Product entity to DTO"""
    return {
        "id": str(product.id),
        "sku": str(product.sku),
        "generic_name": product.generic_name,
        "trade_name": product.trade_name,
        "dosage_form": str(product.dosage_form),
        "dosage_strength": str(product.dosage_strength),
        "manufacturer": product.manufacturer.name,
        "country": product.manufacturer.country,
        "price": product.price.amount,
        "currency": product.price.currency,
        "atc_code": str(product.atc_code),
        "category": product.category,
        "active": product.active,
        "total_quantity": product.total_quantity.value,
        "unit": product.total_quantity.unit,
        "min_stock_level": product.min_stock_level.value,
        "reorder_point": product.reorder_point.value,
        "requires_prescription": product.prescription_requirement.requires_prescription,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }


class GetProductByIdQueryHandler:
    """Handle: GetProductByIdQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: GetProductByIdQuery) -> dict:
        try:
            product = self.product_repo.get_by_id(ProductId(query.product_id))
            if not product:
                return None
            return _product_to_dto(product)
        except Exception as e:
            raise Exception(f"Error fetching product: {str(e)}")


class GetProductBySKUQueryHandler:
    """Handle: GetProductBySKUQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: GetProductBySKUQuery) -> dict:
        try:
            product = self.product_repo.get_by_sku(SKU(query.sku))
            if not product:
                return None
            return _product_to_dto(product)
        except Exception as e:
            raise Exception(f"Error fetching product: {str(e)}")


class GetProductByATCQueryHandler:
    """Handle: GetProductByATCQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: GetProductByATCQuery) -> list:
        try:
            products = self.product_repo.get_by_atc_code(ATCCode(query.atc_code))
            return [_product_to_dto(p) for p in products]
        except Exception as e:
            raise Exception(f"Error fetching products: {str(e)}")


class ListAllProductsQueryHandler:
    """Handle: ListAllProductsQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: ListAllProductsQuery) -> dict:
        try:
            all_products = self.product_repo.list_all()
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = all_products[start:end]
            
            return {
                "products": [_product_to_dto(p) for p in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(all_products),
                "total_pages": (len(all_products) + query.page_size - 1) // query.page_size,
            }
        except Exception as e:
            raise Exception(f"Error fetching products: {str(e)}")


class ListActiveProductsQueryHandler:
    """Handle: ListActiveProductsQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: ListActiveProductsQuery) -> dict:
        try:
            active_products = self.product_repo.list_active()
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = active_products[start:end]
            
            return {
                "products": [_product_to_dto(p) for p in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(active_products),
                "total_pages": (len(active_products) + query.page_size - 1) // query.page_size,
            }
        except Exception as e:
            raise Exception(f"Error fetching products: {str(e)}")


class ListLowStockProductsQueryHandler:
    """Handle: ListLowStockProductsQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: ListLowStockProductsQuery) -> dict:
        try:
            low_stock = self.product_repo.list_low_stock(query.threshold)
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = low_stock[start:end]
            
            return {
                "products": [_product_to_dto(p) for p in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(low_stock),
                "threshold": query.threshold,
            }
        except Exception as e:
            raise Exception(f"Error fetching low stock products: {str(e)}")


class SearchProductsQueryHandler:
    """Handle: SearchProductsQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: SearchProductsQuery) -> dict:
        try:
            results = self.product_repo.search_by_name(query.search_term)
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = results[start:end]
            
            return {
                "search_term": query.search_term,
                "products": [_product_to_dto(p) for p in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(results),
            }
        except Exception as e:
            raise Exception(f"Error searching products: {str(e)}")


class GetProductsByCategoryQueryHandler:
    """Handle: GetProductsByCategoryQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: GetProductsByCategoryQuery) -> dict:
        try:
            products = self.product_repo.search_by_category(query.category)
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = products[start:end]
            
            return {
                "category": query.category,
                "products": [_product_to_dto(p) for p in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(products),
            }
        except Exception as e:
            raise Exception(f"Error fetching products by category: {str(e)}")


class GetProductInventoryQueryHandler:
    """Handle: GetProductInventoryQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: GetProductInventoryQuery) -> dict:
        try:
            product = self.product_repo.get_by_id(ProductId(query.product_id))
            if not product:
                return None
            
            return {
                "product": _product_to_dto(product),
                "inventory": {
                    "total_quantity": product.total_quantity.value,
                    "batches": [
                        {
                            "batch_number": str(b.batch_number),
                            "quantity": b.quantity.value,
                            "expiry_date": b.expiry_date.value.isoformat(),
                            "days_until_expiry": b.days_until_expiry(),
                            "is_expired": b.is_expired(),
                            "received_date": b.received_date.isoformat(),
                        }
                        for b in product.batches
                    ],
                    "total_value": product.get_total_value(),
                },
            }
        except Exception as e:
            raise Exception(f"Error fetching inventory: {str(e)}")


class GetExpiringProductsQueryHandler:
    """Handle: GetExpiringProductsQuery"""
    
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo
    
    def handle(self, query: GetExpiringProductsQuery) -> dict:
        try:
            all_products = self.product_repo.list_all()
            expiring_products = []
            
            for product in all_products:
                expiring_batches = product.get_expiring_soon(query.days_threshold)
                if expiring_batches:
                    expiring_products.append({
                        "product": _product_to_dto(product),
                        "expiring_batches": [
                            {
                                "batch_number": str(b.batch_number),
                                "quantity": b.quantity.value,
                                "expiry_date": b.expiry_date.value.isoformat(),
                                "days_until_expiry": b.days_until_expiry(),
                            }
                            for b in expiring_batches
                        ],
                    })
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = expiring_products[start:end]
            
            return {
                "days_threshold": query.days_threshold,
                "products": paginated,
                "page": query.page,
                "page_size": query.page_size,
                "total": len(expiring_products),
            }
        except Exception as e:
            raise Exception(f"Error fetching expiring products: {str(e)}")
