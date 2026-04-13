"""
Pharmacy Domain - Repository Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from shared_ddd.base import IRepository
from .entities import Product
from .value_objects import ProductId, SKU, ATCCode


class IProductRepository(IRepository, ABC):
    """Repository interface for Product aggregate"""
    
    @abstractmethod
    def add(self, product: Product) -> None:
        """Save a new product"""
        pass
    
    @abstractmethod
    def update(self, product: Product) -> None:
        """Update an existing product"""
        pass
    
    @abstractmethod
    def remove(self, product: Product) -> None:
        """Remove a product"""
        pass
    
    @abstractmethod
    def get_by_id(self, product_id: ProductId) -> Optional[Product]:
        """Get product by ID"""
        pass
    
    @abstractmethod
    def get_by_sku(self, sku: SKU) -> Optional[Product]:
        """Get product by SKU"""
        pass
    
    @abstractmethod
    def get_by_atc_code(self, atc_code: ATCCode) -> List[Product]:
        """Get products by ATC code"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Product]:
        """Get all products"""
        pass
    
    @abstractmethod
    def list_active(self) -> List[Product]:
        """Get all active products"""
        pass
    
    @abstractmethod
    def list_low_stock(self, threshold: int) -> List[Product]:
        """Get products with low stock"""
        pass
    
    @abstractmethod
    def search_by_name(self, name: str) -> List[Product]:
        """Search products by generic or trade name"""
        pass
    
    @abstractmethod
    def search_by_category(self, category: str) -> List[Product]:
        """Search products by category"""
        pass
