"""
Dispensing Service Domain Layer
Order context: managing customer orders, line items, and dispensing
"""

from .value_objects import (
    OrderStatus, OrderId, CustomerId, ProductId, Money, Quantity, LineItem,
    ShippingAddress, PaymentInfo, PrescriptionInfo, PaymentStatus, PaymentMethod
)

from .entities import Order, OrderItem

from .events import (
    OrderCreated, OrderConfirmed, OrderItemDispensed, OrderFullyDispensed,
    OrderPaymentProcessed, OrderPaymentFailed, OrderLineItemAdded,
    OrderLineItemRemoved, OrderCancelled, OrderStatusChanged, OrderOnHold,
    OrderResumed, ShippingAddressChanged, PrescriptionValidationFailed
)

from .repositories import IOrderRepository

from .domain_services import (
    OrderCreationService,
    OrderProcessingService,
    OrderPaymentService,
    PrescriptionValidationService
)

__all__ = [
    # Value Objects
    "OrderStatus",
    "OrderId",
    "CustomerId",
    "ProductId",
    "Money",
    "Quantity",
    "LineItem",
    "ShippingAddress",
    "PaymentInfo",
    "PrescriptionInfo",
    "PaymentStatus",
    "PaymentMethod",
    # Entities
    "Order",
    "OrderItem",
    # Events
    "OrderCreated",
    "OrderConfirmed",
    "OrderItemDispensed",
    "OrderFullyDispensed",
    "OrderPaymentProcessed",
    "OrderPaymentFailed",
    "OrderLineItemAdded",
    "OrderLineItemRemoved",
    "OrderCancelled",
    "OrderStatusChanged",
    "OrderOnHold",
    "OrderResumed",
    "ShippingAddressChanged",
    "PrescriptionValidationFailed",
    # Repository
    "IOrderRepository",
    # Domain Services
    "OrderCreationService",
    "OrderProcessingService",
    "OrderPaymentService",
    "PrescriptionValidationService",
]
