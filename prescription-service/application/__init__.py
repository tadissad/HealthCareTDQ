"""
Prescription Service Application Layer
"""

from .commands import (
    CreatePrescriptionCommand, AddCartItemCommand, RemoveCartItemCommand,
    UpdateCartItemQuantityCommand, SubmitPrescriptionCommand,
    ConfirmPrescriptionCommand, FulfillPrescriptionItemCommand,
    CancelPrescriptionCommand, ClearCartCommand,
    CreatePrescriptionResult, CartOperationResult,
    PrescriptionStatusChangeResult, FulfillmentResult
)

from .command_handlers import (
    CreatePrescriptionHandler, AddCartItemHandler, RemoveCartItemHandler,
    UpdateCartItemQuantityHandler, SubmitPrescriptionHandler,
    ConfirmPrescriptionHandler, FulfillPrescriptionItemHandler,
    CancelPrescriptionHandler, ClearCartHandler
)

from .queries import (
    GetPrescriptionByIdQuery, GetPrescriptionsByCustomerQuery,
    ListPrescriptionsByStatusQuery, ListDraftPrescriptionsQuery,
    ListSubmittedPrescriptionsQuery, ListActivePrescriptionsQuery,
    ListRecentPrescriptionsQuery, SearchPrescriptionQuery,
    GetPrescriptionItemsQuery, CheckPrescriptionValidityQuery,
    CartItemDTO, DrugRequirementDTO, PrescriptionLineItemDTO,
    PrescriberDTO, DiagnosisDTO, PrescriptionValidityDTO,
    PrescriptionDetailDTO, PrescriptionSummaryDTO, PrescriptionListDTO,
    PrescriptionCheckDTO
)

from .query_handlers import (
    GetPrescriptionByIdHandler, GetPrescriptionsByCustomerHandler,
    ListPrescriptionsByStatusHandler, ListDraftPrescriptionsHandler,
    ListSubmittedPrescriptionsHandler, ListActivePrescriptionsHandler,
    ListRecentPrescriptionsHandler, SearchPrescriptionHandler,
    GetPrescriptionItemsHandler, CheckPrescriptionValidityHandler
)

__all__ = [
    # Commands
    "CreatePrescriptionCommand",
    "AddCartItemCommand",
    "RemoveCartItemCommand",
    "UpdateCartItemQuantityCommand",
    "SubmitPrescriptionCommand",
    "ConfirmPrescriptionCommand",
    "FulfillPrescriptionItemCommand",
    "CancelPrescriptionCommand",
    "ClearCartCommand",
    # Command Results
    "CreatePrescriptionResult",
    "CartOperationResult",
    "PrescriptionStatusChangeResult",
    "FulfillmentResult",
    # Command Handlers
    "CreatePrescriptionHandler",
    "AddCartItemHandler",
    "RemoveCartItemHandler",
    "UpdateCartItemQuantityHandler",
    "SubmitPrescriptionHandler",
    "ConfirmPrescriptionHandler",
    "FulfillPrescriptionItemHandler",
    "CancelPrescriptionHandler",
    "ClearCartHandler",
    # Queries
    "GetPrescriptionByIdQuery",
    "GetPrescriptionsByCustomerQuery",
    "ListPrescriptionsByStatusQuery",
    "ListDraftPrescriptionsQuery",
    "ListSubmittedPrescriptionsQuery",
    "ListActivePrescriptionsQuery",
    "ListRecentPrescriptionsQuery",
    "SearchPrescriptionQuery",
    "GetPrescriptionItemsQuery",
    "CheckPrescriptionValidityQuery",
    # Query DTOs
    "CartItemDTO",
    "DrugRequirementDTO",
    "PrescriptionLineItemDTO",
    "PrescriberDTO",
    "DiagnosisDTO",
    "PrescriptionValidityDTO",
    "PrescriptionDetailDTO",
    "PrescriptionSummaryDTO",
    "PrescriptionListDTO",
    "PrescriptionCheckDTO",
    # Query Handlers
    "GetPrescriptionByIdHandler",
    "GetPrescriptionsByCustomerHandler",
    "ListPrescriptionsByStatusHandler",
    "ListDraftPrescriptionsHandler",
    "ListSubmittedPrescriptionsHandler",
    "ListActivePrescriptionsHandler",
    "ListRecentPrescriptionsHandler",
    "SearchPrescriptionHandler",
    "GetPrescriptionItemsHandler",
    "CheckPrescriptionValidityHandler",
]
