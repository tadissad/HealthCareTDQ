"""
Dispensing Service Application Layer
Order management commands and queries with CQRS pattern
"""

from .commands import (
    CreateOrderCommand,
    ConfirmOrderCommand,
    DispenseOrderItemCommand,
    ProcessPaymentCommand,
    HandlePaymentFailureCommand,
    CancelOrderCommand,
    PutOrderOnHoldCommand,
    ResumeOrderCommand,
    UpdateShippingAddressCommand,
    RemoveOrderLineItemCommand,
    ApplyDiscountToOrderCommand,
    ValidatePrescriptionCommand,
)

from .command_handlers import (
    CreateOrderCommandHandler,
    ConfirmOrderCommandHandler,
    DispenseOrderItemCommandHandler,
    ProcessPaymentCommandHandler,
    HandlePaymentFailureCommandHandler,
    CancelOrderCommandHandler,
    PutOrderOnHoldCommandHandler,
    ResumeOrderCommandHandler,
    UpdateShippingAddressCommandHandler,
    RemoveOrderLineItemCommandHandler,
    ApplyDiscountToOrderCommandHandler,
    ValidatePrescriptionCommandHandler,
)

from .queries import (
    GetOrderByIdQuery,
    GetOrdersByCustomerQuery,
    ListPendingOrdersQuery,
    ListOrdersReadyForDispensingQuery,
    ListDispensingOrdersQuery,
    ListOrdersByStatusQuery,
    ListAllOrdersQuery,
    SearchOrdersByCustomerAndStatusQuery,
    ListOrdersWithPrescriptionQuery,
    GetRecentOrdersQuery,
    GetOrderInventoryQuery,
    SearchOrdersQuery,
)

from .query_handlers import (
    GetOrderByIdQueryHandler,
    GetOrdersByCustomerQueryHandler,
    ListPendingOrdersQueryHandler,
    ListOrdersReadyForDispensingQueryHandler,
    ListDispensingOrdersQueryHandler,
    ListOrdersByStatusQueryHandler,
    ListAllOrdersQueryHandler,
    SearchOrdersByCustomerAndStatusQueryHandler,
    ListOrdersWithPrescriptionQueryHandler,
    GetRecentOrdersQueryHandler,
    GetOrderInventoryQueryHandler,
)

__all__ = [
    # Commands
    "CreateOrderCommand",
    "ConfirmOrderCommand",
    "DispenseOrderItemCommand",
    "ProcessPaymentCommand",
    "HandlePaymentFailureCommand",
    "CancelOrderCommand",
    "PutOrderOnHoldCommand",
    "ResumeOrderCommand",
    "UpdateShippingAddressCommand",
    "RemoveOrderLineItemCommand",
    "ApplyDiscountToOrderCommand",
    "ValidatePrescriptionCommand",
    # Command Handlers
    "CreateOrderCommandHandler",
    "ConfirmOrderCommandHandler",
    "DispenseOrderItemCommandHandler",
    "ProcessPaymentCommandHandler",
    "HandlePaymentFailureCommandHandler",
    "CancelOrderCommandHandler",
    "PutOrderOnHoldCommandHandler",
    "ResumeOrderCommandHandler",
    "UpdateShippingAddressCommandHandler",
    "RemoveOrderLineItemCommandHandler",
    "ApplyDiscountToOrderCommandHandler",
    "ValidatePrescriptionCommandHandler",
    # Queries
    "GetOrderByIdQuery",
    "GetOrdersByCustomerQuery",
    "ListPendingOrdersQuery",
    "ListOrdersReadyForDispensingQuery",
    "ListDispensingOrdersQuery",
    "ListOrdersByStatusQuery",
    "ListAllOrdersQuery",
    "SearchOrdersByCustomerAndStatusQuery",
    "ListOrdersWithPrescriptionQuery",
    "GetRecentOrdersQuery",
    "GetOrderInventoryQuery",
    "SearchOrdersQuery",
    # Query Handlers
    "GetOrderByIdQueryHandler",
    "GetOrdersByCustomerQueryHandler",
    "ListPendingOrdersQueryHandler",
    "ListOrdersReadyForDispensingQueryHandler",
    "ListDispensingOrdersQueryHandler",
    "ListOrdersByStatusQueryHandler",
    "ListAllOrdersQueryHandler",
    "SearchOrdersByCustomerAndStatusQueryHandler",
    "ListOrdersWithPrescriptionQueryHandler",
    "GetRecentOrdersQueryHandler",
    "GetOrderInventoryQueryHandler",
]
