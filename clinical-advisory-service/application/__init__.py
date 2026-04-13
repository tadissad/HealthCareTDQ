"""
Clinical-Advisory Service Application Layer
"""

from .commands_queries import (
    # Commands
    InitiateConsultationCommand, AddPatientMessageCommand,
    PerformAIScreeningCommand, AddAIRecommendationCommand,
    RequestClinicianReviewCommand, EndorseRecommendationCommand,
    RejectRecommendationCommand, FinalizeRecommendationsCommand,
    CompleteConsultationCommand, CancelConsultationCommand,
    EscalateUrgentCaseCommand,
    # Queries
    GetConsultationByIdQuery, GetPatientConsultationsQuery,
    ListActiveConsultationsQuery, ListPendingClinicianReviewQuery,
    ListUrgentCasesQuery, GetConsultationMessagesQuery,
    GetRecommendationsQuery, GetConsultationStatsQuery,
    SearchConsultationsQuery,
    # Result DTOs
    ConsultationInitiatedResult, MessageAddedResult,
    ScreeningCompletedResult, RecommendationAddedResult,
    ConsultationActionResult, ConsultationDetailDTO,
    ConsultationSummaryDTO, ConsultationListDTO,
    MessageDTO, RecommendationDTO
)

from .handlers import (
    # Command Handlers
    InitiateConsultationHandler, AddPatientMessageHandler,
    PerformAIScreeningHandler, AddAIRecommendationHandler,
    EndorseRecommendationHandler, RequestClinicianReviewHandler,
    CompleteConsultationHandler, EscalateUrgentCaseHandler,
    # Query Handlers
    GetConsultationByIdHandler, GetPatientConsultationsHandler,
    ListActiveConsultationsHandler, ListUrgentCasesHandler
)

__all__ = [
    # Commands
    "InitiateConsultationCommand",
    "AddPatientMessageCommand",
    "PerformAIScreeningCommand",
    "AddAIRecommendationCommand",
    "RequestClinicianReviewCommand",
    "EndorseRecommendationCommand",
    "RejectRecommendationCommand",
    "FinalizeRecommendationsCommand",
    "CompleteConsultationCommand",
    "CancelConsultationCommand",
    "EscalateUrgentCaseCommand",
    # Queries
    "GetConsultationByIdQuery",
    "GetPatientConsultationsQuery",
    "ListActiveConsultationsQuery",
    "ListPendingClinicianReviewQuery",
    "ListUrgentCasesQuery",
    "GetConsultationMessagesQuery",
    "GetRecommendationsQuery",
    "GetConsultationStatsQuery",
    "SearchConsultationsQuery",
    # Result DTOs
    "ConsultationInitiatedResult",
    "MessageAddedResult",
    "ScreeningCompletedResult",
    "RecommendationAddedResult",
    "ConsultationActionResult",
    "ConsultationDetailDTO",
    "ConsultationSummaryDTO",
    "ConsultationListDTO",
    "MessageDTO",
    "RecommendationDTO",
    # Command Handlers
    "InitiateConsultationHandler",
    "AddPatientMessageHandler",
    "PerformAIScreeningHandler",
    "AddAIRecommendationHandler",
    "EndorseRecommendationHandler",
    "RequestClinicianReviewHandler",
    "CompleteConsultationHandler",
    "EscalateUrgentCaseHandler",
    # Query Handlers
    "GetConsultationByIdHandler",
    "GetPatientConsultationsHandler",
    "ListActiveConsultationsHandler",
    "ListUrgentCasesHandler",
]
