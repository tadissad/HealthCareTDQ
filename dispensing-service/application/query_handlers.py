"""
Dispensing Service Application Layer - Query Handlers
Read operations returning OrderDTO
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from .queries import (
    GetOrderByIdQuery, GetOrdersByCustomerQuery, ListPendingOrdersQuery,
    ListOrdersReadyForDispensingQuery, ListDispensingOrdersQuery,
    ListOrdersByStatusQuery, ListAllOrdersQuery,
    SearchOrdersByCustomerAndStatusQuery, ListOrdersWithPrescriptionQuery,
    GetRecentOrdersQuery, GetOrderInventoryQuery, SearchOrdersQuery
)
from ..domain import (
    OrderId, CustomerId, OrderStatus, IOrderRepository
)


def _order_to_dto(order) -> dict:
    """Transform Order entity to DTO"""
    return {
        "order_id": str(order.order_id),
        "customer_id": str(order.customer_id),
        "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
        "total_amount": order.total_amount.amount,
        "currency": order.total_amount.currency,
        "discount_amount": order.discount_amount.amount if order.discount_amount else 0,
        "amount_after_discount": order.get_total_after_discount().amount,
        "line_items_count": len(order.order_items),
        "order_date": order.order_date.isoformat(),
        "confirmed_date": order.confirmed_date.isoformat() if order.confirmed_date else None,
        "dispensed_date": order.dispensed_date.isoformat() if order.dispensed_date else None,
        "payment_status": order.payment_info.status.value if order.payment_info else "UNKNOWN",
        "payment_method": order.payment_info.method.value if order.payment_info else "UNKNOWN",
        "has_prescription": order.prescription_info is not None,
        "has_shipping_address": order.shipping_address is not None,
        "notes": order.notes,
    }


class GetOrderByIdQueryHandler:
    """Handle: GetOrderByIdQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: GetOrderByIdQuery) -> dict:
        try:
            order = self.order_repo.get_by_id(OrderId(query.order_id))
            if not order:
                return None
            
            dto = _order_to_dto(order)
            
            # Add line items
            dto["line_items"] = [
                {
                    "sku": item.line_item.sku,
                    "product_name": item.line_item.product_name,
                    "quantity_ordered": item.line_item.quantity.value,
                    "quantity_dispensed": item.dispensed_quantity.value,
                    "unit_price": item.line_item.unit_price.amount,
                    "line_total": item.line_item.line_total.amount,
                    "is_fully_dispensed": item.is_fully_dispensed(),
                }
                for item in order.order_items
            ]
            
            if order.shipping_address:
                dto["shipping_address"] = order.shipping_address.format_address()
            
            if order.prescription_info:
                dto["prescription"] = {
                    "prescription_id": order.prescription_info.prescription_id,
                    "prescriber": order.prescription_info.prescriber_name,
                    "valid_until": order.prescription_info.valid_until.isoformat(),
                    "is_valid": order.prescription_info.is_valid(),
                    "days_until_expiry": order.prescription_info.days_until_expiry(),
                }
            
            return dto
        
        except Exception as e:
            raise Exception(f"Error fetching order: {str(e)}")


class GetOrdersByCustomerQueryHandler:
    """Handle: GetOrdersByCustomerQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: GetOrdersByCustomerQuery) -> dict:
        try:
            orders = self.order_repo.get_by_customer_id(CustomerId(query.customer_id))
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = orders[start:end]
            
            return {
                "customer_id": query.customer_id,
                "orders": [_order_to_dto(o) for o in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(orders),
                "total_pages": (len(orders) + query.page_size - 1) // query.page_size,
            }
        
        except Exception as e:
            raise Exception(f"Error fetching customer orders: {str(e)}")


class ListPendingOrdersQueryHandler:
    """Handle: ListPendingOrdersQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: ListPendingOrdersQuery) -> dict:
        try:
            orders = self.order_repo.list_pending_orders()
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = orders[start:end]
            
            return {
                "status": "PENDING",
                "orders": [_order_to_dto(o) for o in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(orders),
            }
        
        except Exception as e:
            raise Exception(f"Error fetching pending orders: {str(e)}")


class ListOrdersReadyForDispensingQueryHandler:
    """Handle: ListOrdersReadyForDispensingQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: ListOrdersReadyForDispensingQuery) -> dict:
        try:
            orders = self.order_repo.list_orders_ready_for_dispensing()
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = orders[start:end]
            
            return {
                "status": "CONFIRMED",
                "orders": [_order_to_dto(o) for o in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(orders),
            }
        
        except Exception as e:
            raise Exception(f"Error fetching ready orders: {str(e)}")


class ListDispensingOrdersQueryHandler:
    """Handle: ListDispensingOrdersQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: ListDispensingOrdersQuery) -> dict:
        try:
            orders = self.order_repo.list_dispensing_orders()
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = orders[start:end]
            
            return {
                "status": "DISPENSING",
                "orders": [_order_to_dto(o) for o in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(orders),
            }
        
        except Exception as e:
            raise Exception(f"Error fetching dispensing orders: {str(e)}")


class ListOrdersByStatusQueryHandler:
    """Handle: ListOrdersByStatusQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: ListOrdersByStatusQuery) -> dict:
        try:
            status = OrderStatus[query.status.upper()]
            orders = self.order_repo.list_by_status(status)
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = orders[start:end]
            
            return {
                "status": query.status,
                "orders": [_order_to_dto(o) for o in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(orders),
            }
        
        except Exception as e:
            raise Exception(f"Error fetching orders: {str(e)}")


class ListAllOrdersQueryHandler:
    """Handle: ListAllOrdersQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: ListAllOrdersQuery) -> dict:
        try:
            all_orders = self.order_repo.list_all()
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = all_orders[start:end]
            
            return {
                "orders": [_order_to_dto(o) for o in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(all_orders),
                "total_pages": (len(all_orders) + query.page_size - 1) // query.page_size,
            }
        
        except Exception as e:
            raise Exception(f"Error fetching orders: {str(e)}")


class SearchOrdersByCustomerAndStatusQueryHandler:
    """Handle: SearchOrdersByCustomerAndStatusQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: SearchOrdersByCustomerAndStatusQuery) -> dict:
        try:
            status = OrderStatus[query.status.upper()]
            orders = self.order_repo.search_by_customer_and_status(
                CustomerId(query.customer_id),
                status
            )
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = orders[start:end]
            
            return {
                "customer_id": query.customer_id,
                "status": query.status,
                "orders": [_order_to_dto(o) for o in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(orders),
            }
        
        except Exception as e:
            raise Exception(f"Error searching orders: {str(e)}")


class ListOrdersWithPrescriptionQueryHandler:
    """Handle: ListOrdersWithPrescriptionQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: ListOrdersWithPrescriptionQuery) -> dict:
        try:
            orders = self.order_repo.list_orders_with_prescription()
            
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = orders[start:end]
            
            return {
                "filter": "Has prescription",
                "orders": [_order_to_dto(o) for o in paginated],
                "page": query.page,
                "page_size": query.page_size,
                "total": len(orders),
            }
        
        except Exception as e:
            raise Exception(f"Error fetching prescription orders: {str(e)}")


class GetRecentOrdersQueryHandler:
    """Handle: GetRecentOrdersQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: GetRecentOrdersQuery) -> dict:
        try:
            orders = self.order_repo.list_recent_orders(query.limit)
            
            return {
                "recent_orders": [_order_to_dto(o) for o in orders],
                "count": len(orders),
            }
        
        except Exception as e:
            raise Exception(f"Error fetching recent orders: {str(e)}")


class GetOrderInventoryQueryHandler:
    """Handle: GetOrderInventoryQuery"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, query: GetOrderInventoryQuery) -> dict:
        try:
            order = self.order_repo.get_by_id(OrderId(query.order_id))
            
            if not order:
                return None
            
            return {
                "order_id": str(order.order_id),
                "line_items": [
                    {
                        "product_id": str(item.line_item.product_id),
                        "sku": item.line_item.sku,
                        "product_name": item.line_item.product_name,
                        "quantity_ordered": item.line_item.quantity.value,
                        "quantity_dispensed": item.dispensed_quantity.value,
                        "quantity_remaining": item.remaining_quantity().value,
                        "unit_price": item.line_item.unit_price.amount,
                        "line_total": item.line_item.line_total.amount,
                        "dispensed_total": item.get_dispersed_total().amount,
                        "is_fully_dispensed": item.is_fully_dispensed(),
                    }
                    for item in order.order_items
                ],
                "summary": {
                    "total_items": len(order.order_items),
                    "fully_dispensed_items": sum(1 for item in order.order_items if item.is_fully_dispensed()),
                    "partially_dispensed": order.is_partially_dispensed(),
                    "total_value": order.total_amount.amount,
                    "dispensed_value": order.get_dispensed_total().amount,
                },
            }
        
        except Exception as e:
            raise Exception(f"Error fetching order inventory: {str(e)}")
