"""
Pharmacy Application Layer - Queries

Queries are read-only requests
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetProductByIdQuery:
    """Query: Get product by ID"""
    product_id: str


@dataclass
class GetProductBySKUQuery:
    """Query: Get product by SKU"""
    sku: str


@dataclass
class GetProductByATCQuery:
    """Query: Get products by ATC code"""
    atc_code: str


@dataclass
class ListAllProductsQuery:
    """Query: List all products with pagination"""
    page: int = 1
    page_size: int = 20


@dataclass
class ListActiveProductsQuery:
    """Query: List active products"""
    page: int = 1
    page_size: int = 20


@dataclass
class ListLowStockProductsQuery:
    """Query: Get products with low stock"""
    threshold: int = 20
    page: int = 1
    page_size: int = 20


@dataclass
class SearchProductsQuery:
    """Query: Search products by name"""
    search_term: str
    page: int = 1
    page_size: int = 20


@dataclass
class GetProductsByCategoryQuery:
    """Query: Get products by category"""
    category: str
    page: int = 1
    page_size: int = 20


@dataclass
class GetProductInventoryQuery:
    """Query: Get detailed inventory info for product"""
    product_id: str


@dataclass
class GetExpiringProductsQuery:
    """Query: Get products expiring soon"""
    days_threshold: int = 90
    page: int = 1
    page_size: int = 20
