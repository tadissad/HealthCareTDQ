"""
Pharmacy Application Layer
Commands and Queries for product management following CQRS pattern
"""

from .commands import (
    CreateProductCommand,
    ReceiveInventoryCommand,
    SellProductCommand,
    ScrapProductCommand,
    ChangePriceCommand,
    AdjustMinStockCommand,
    ChangeManufacturerCommand,
    CheckExpiringProductsCommand,
    DeactivateProductCommand,
)

from .command_handlers import (
    CreateProductCommandHandler,
    ReceiveInventoryCommandHandler,
    SellProductCommandHandler,
    ScrapProductCommandHandler,
    ChangePriceCommandHandler,
    AdjustMinStockCommandHandler,
    ChangeManufacturerCommandHandler,
    CheckExpiringProductsCommandHandler,
    DeactivateProductCommandHandler,
)

from .queries import (
    GetProductByIdQuery,
    GetProductBySKUQuery,
    GetProductByATCQuery,
    ListAllProductsQuery,
    ListActiveProductsQuery,
    ListLowStockProductsQuery,
    SearchProductsQuery,
    GetProductsByCategoryQuery,
    GetProductInventoryQuery,
    GetExpiringProductsQuery,
)

from .query_handlers import (
    GetProductByIdQueryHandler,
    GetProductBySKUQueryHandler,
    GetProductByATCQueryHandler,
    ListAllProductsQueryHandler,
    ListActiveProductsQueryHandler,
    ListLowStockProductsQueryHandler,
    SearchProductsQueryHandler,
    GetProductsByCategoryQueryHandler,
    GetProductInventoryQueryHandler,
    GetExpiringProductsQueryHandler,
)

__all__ = [
    # Commands
    "CreateProductCommand",
    "ReceiveInventoryCommand",
    "SellProductCommand",
    "ScrapProductCommand",
    "ChangePriceCommand",
    "AdjustMinStockCommand",
    "ChangeManufacturerCommand",
    "CheckExpiringProductsCommand",
    "DeactivateProductCommand",
    # Command Handlers
    "CreateProductCommandHandler",
    "ReceiveInventoryCommandHandler",
    "SellProductCommandHandler",
    "ScrapProductCommandHandler",
    "ChangePriceCommandHandler",
    "AdjustMinStockCommandHandler",
    "ChangeManufacturerCommandHandler",
    "CheckExpiringProductsCommandHandler",
    "DeactivateProductCommandHandler",
    # Queries
    "GetProductByIdQuery",
    "GetProductBySKUQuery",
    "GetProductByATCQuery",
    "ListAllProductsQuery",
    "ListActiveProductsQuery",
    "ListLowStockProductsQuery",
    "SearchProductsQuery",
    "GetProductsByCategoryQuery",
    "GetProductInventoryQuery",
    "GetExpiringProductsQuery",
    # Query Handlers
    "GetProductByIdQueryHandler",
    "GetProductBySKUQueryHandler",
    "GetProductByATCQueryHandler",
    "ListAllProductsQueryHandler",
    "ListActiveProductsQueryHandler",
    "ListLowStockProductsQueryHandler",
    "SearchProductsQueryHandler",
    "GetProductsByCategoryQueryHandler",
    "GetProductInventoryQueryHandler",
    "GetExpiringProductsQueryHandler",
]
