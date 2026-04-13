"""
Medical-Catalog Service - Complete Domain Layer
Product catalog with search, filtering, and inventory
"""

from shared_ddd.base import ValueObject, Aggregate, DomainEvent, DomainService, IRepository
from dataclasses import dataclass
from typing import Optional, List
import time


# ============ VALUE OBJECTS ============

class ProductId(ValueObject):
    def __init__(self, value: str):
        self.value = str(value)
    def __eq__(self, other):
        return isinstance(other, ProductId) and self.value == other.value
    def __hash__(self):
        return hash(self.value)


class ProductCode(ValueObject):
    def __init__(self, value: str):
        if not value or len(value) < 2:
            raise ValueError("Invalid product code")
        self.value = value.upper()
    def __eq__(self, other):
        return isinstance(other, ProductCode) and self.value == other.value
    def __hash__(self):
        return hash(self.value)


class ProductPrice(ValueObject):
    def __init__(self, amount: float, currency: str = "VND"):
        if amount < 0:
            raise ValueError("Price cannot be negative")
        self.amount = amount
        self.currency = currency
    def __eq__(self, other):
        return isinstance(other, ProductPrice) and self.amount == other.amount
    def __hash__(self):
        return hash(self.amount)


class ProductStock(ValueObject):
    def __init__(self, quantity: int, unit: str = "unit"):
        if quantity < 0:
            raise ValueError("Stock cannot be negative")
        self.quantity = quantity
        self.unit = unit
    def __eq__(self, other):
        return isinstance(other, ProductStock) and self.quantity == other.quantity


class ProductCategory(ValueObject):
    VALID_CATEGORIES = [
        'PRESCRIPTION_DRUG',
        'OTC_DRUG',
        'SUPPLEMENT',
        'MEDICAL_DEVICE',
        'WELLNESS',
        'DIAGNOSTIC'
    ]
    def __init__(self, category: str):
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        self.value = category
    def __eq__(self, other):
        return isinstance(other, ProductCategory) and self.value == other.value
    def __hash__(self):
        return hash(self.value)


# ============ EVENTS ============

@dataclass
class ProductAdded(DomainEvent):
    product_id: str
    name: str
    category: str
    price: float
    timestamp: int
    event_type: str = "ProductAdded"

@dataclass
class ProductUpdated(DomainEvent):
    product_id: str
    updated_fields: List[str]
    timestamp: int
    event_type: str = "ProductUpdated"

@dataclass
class ProductRemoved(DomainEvent):
    product_id: str
    timestamp: int
    event_type: str = "ProductRemoved"

@dataclass
class PriceChanged(DomainEvent):
    product_id: str
    old_price: float
    new_price: float
    timestamp: int
    event_type: str = "PriceChanged"


# ============ ENTITIES ============

class Product(Aggregate):
    """Product aggregate"""
    def __init__(self, product_id: ProductId, code: ProductCode, name: str,
                 category: ProductCategory, price: ProductPrice):
        super().__init__()
        self.product_id = product_id
        self.code = code
        self.name = name
        self.category = category
        self.price = price
        self.description = ""
        self.stock = ProductStock(0)
        self.is_active = True
        self.created_at = int(time.time())
        
        self.domain_events.append(ProductAdded(
            product_id=product_id.value,
            name=name,
            category=category.value,
            price=price.amount,
            timestamp=self.created_at
        ))
    
    def update_price(self, new_price: ProductPrice):
        """Update product price"""
        old_price = self.price.amount
        self.price = new_price
        self.domain_events.append(PriceChanged(
            product_id=self.product_id.value,
            old_price=old_price,
            new_price=new_price.amount,
            timestamp=int(time.time())
        ))
    
    def update_stock(self, quantity: int):
        """Update product stock"""
        self.stock = ProductStock(quantity)
    
    def deactivate(self):
        """Deactivate product"""
        self.is_active = False
    
    def activate(self):
        """Activate product"""
        self.is_active = True


# ============ REPOSITORIES ============

class IProductRepository(IRepository):
    def save(self, product: Product) -> None: pass
    def get_by_id(self, product_id: ProductId) -> Optional[Product]: pass
    def get_by_code(self, code: ProductCode) -> Optional[Product]: pass
    def search_by_name(self, name: str, limit: int = 50) -> List[Product]: pass
    def get_by_category(self, category: ProductCategory, limit: int = 100) -> List[Product]: pass
    def list_active_products(self, limit: int = 100) -> List[Product]: pass


# ============ DOMAIN SERVICES ============

class ProductSearchService(DomainService):
    """Product search operations"""
    def __init__(self, product_repo):
        self.product_repo = product_repo
    
    def search_products(self, query: str, category: Optional[str] = None,
                       price_min: float = None, price_max: float = None) -> List[Product]:
        """Search products with filters"""
        results = self.product_repo.search_by_name(query)
        
        if category:
            results = [p for p in results if p.category.value == category]
        
        if price_min:
            results = [p for p in results if p.price.amount >= price_min]
        
        if price_max:
            results = [p for p in results if p.price.amount <= price_max]
        
        return results


class InventoryService(DomainService):
    """Inventory management"""
    def __init__(self, product_repo):
        self.product_repo = product_repo
    
    def check_availability(self, product_id: ProductId, quantity: int) -> bool:
        """Check if product is available"""
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return False
        return product.stock.quantity >= quantity
    
    def get_low_stock_products(self, threshold: int = 20) -> List[Product]:
        """Get products with low stock"""
        products = self.product_repo.list_active_products()
        return [p for p in products if p.stock.quantity < threshold]
