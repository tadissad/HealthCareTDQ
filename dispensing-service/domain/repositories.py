"""
Dispensing Service Domain Layer - Repository Interface
Interface for Order persistence (implemented in infrastructure layer)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from abc import ABC, abstractmethod
from typing import List, Optional

from shared_ddd.base import IRepository
from .value_objects import OrderId, CustomerId, OrderStatus
from .entities import Order


class IOrderRepository(IRepository, ABC):
    """
    Interface for Order repository
    Implemented in infrastructure layer with specific persistence mechanism
    """
    
    @abstractmethod
    def add(self, order: Order) -> None:
        """
        Persist new order to storage
        
        Args:
            order: Order aggregate to save
            
        Raises:
            Exception: If save fails
        """
        pass
    
    @abstractmethod
    def update(self, order: Order) -> None:
        """
        Update existing order in storage
        
        Args:
            order: Order aggregate with updated state
            
        Raises:
            Exception: If order not found or update fails
        """
        pass
    
    @abstractmethod
    def remove(self, order_id: OrderId) -> None:
        """
        Delete order from storage
        
        Args:
            order_id: ID of order to delete
        """
        pass
    
    @abstractmethod
    def get_by_id(self, order_id: OrderId) -> Optional[Order]:
        """
        Retrieve order by ID
        
        Args:
            order_id: Order ID to fetch
            
        Returns:
            Order entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: CustomerId) -> List[Order]:
        """
        Retrieve all orders for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            List of orders for customer, empty list if none
        """
        pass
    
    @abstractmethod
    def list_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Retrieve all orders with specific status
        
        Args:
            status: OrderStatus to filter by
            
        Returns:
            List of orders with matching status
        """
        pass
    
    @abstractmethod
    def list_pending_orders(self) -> List[Order]:
        """Retrieve all pending orders awaiting confirmation"""
        pass
    
    @abstractmethod
    def list_orders_ready_for_dispensing(self) -> List[Order]:
        """Retrieve all confirmed orders ready to dispense"""
        pass
    
    @abstractmethod
    def list_dispensing_orders(self) -> List[Order]:
        """Retrieve all orders currently being dispensed"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Order]:
        """Retrieve all orders"""
        pass
    
    @abstractmethod
    def search_by_customer_and_status(self, customer_id: CustomerId, status: OrderStatus) -> List[Order]:
        """Retrieve orders by customer and status combination"""
        pass
    
    @abstractmethod
    def list_orders_with_prescription(self) -> List[Order]:
        """Retrieve all orders that include prescription items"""
        pass
    
    @abstractmethod
    def list_recent_orders(self, limit: int = 10) -> List[Order]:
        """Retrieve most recent orders"""
        pass
