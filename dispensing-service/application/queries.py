"""
Dispensing Service Application Layer - Queries
CQRS: Queries represent read operations, return DTOs
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetOrderByIdQuery:
    """Query: Get order by ID"""
    order_id: str


@dataclass
class GetOrdersByCustomerQuery:
    """Query: Get all orders for customer"""
    customer_id: str
    page: int = 1
    page_size: int = 20


@dataclass
class ListPendingOrdersQuery:
    """Query: Get all pending orders awaiting confirmation"""
    page: int = 1
    page_size: int = 20


@dataclass
class ListOrdersReadyForDispensingQuery:
    """Query: Get confirmed orders ready to dispense"""
    page: int = 1
    page_size: int = 20


@dataclass
class ListDispensingOrdersQuery:
    """Query: Get orders currently being dispensed"""
    page: int = 1
    page_size: int = 20


@dataclass
class ListOrdersByStatusQuery:
    """Query: Get orders by status"""
    status: str  # PENDING, CONFIRMED, DISPENSING, COMPLETED, CANCELLED, ON_HOLD
    page: int = 1
    page_size: int = 20


@dataclass
class ListAllOrdersQuery:
    """Query: Get all orders"""
    page: int = 1
    page_size: int = 20


@dataclass
class SearchOrdersByCustomerAndStatusQuery:
    """Query: Get orders by customer and status"""
    customer_id: str
    status: str
    page: int = 1
    page_size: int = 20


@dataclass
class ListOrdersWithPrescriptionQuery:
    """Query: Get all orders with prescription items"""
    page: int = 1
    page_size: int = 20


@dataclass
class GetRecentOrdersQuery:
    """Query: Get most recent orders"""
    limit: int = 10


@dataclass
class GetOrderInventoryQuery:
    """Query: Get detailed inventory/line items for order"""
    order_id: str


@dataclass
class SearchOrdersQuery:
    """Query: Search orders by various criteria"""
    search_term: Optional[str] = None
    customer_id: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20
