"""
Clinical-Advisory Service Domain Layer
"""

from .value_objects import (
    ConsultationStatus, MessageType, RecommendationType,
    ConsultationId, PatientId, ClinicianId, ConsultationMessage,
    MedicalBackground, Symptom, SymptomProfile, MedicalRecommendation,
    KnowledgeGraphNode, VectorSearchResult, ConsultationStats
)

from .entities import Consultation, ConversationThread

from .events import (
    ConsultationInitiated, AwaitingClinicianReview, ConsultationStarted,
    ConsultationCompleted, ConsultationCancelled, PatientMessageAdded,
    AIScreeningCompleted, AIQuestionAsked, ClinicianMessageAdded,
    AIRecommendationGenerated, RecommendationEndorsed, RecommendationRejected,
    RecommendationsFinalized, UrgentCaseDetected, ConsultationEscalated,
    PersonalDataRequested
)

from .repositories import IClinicalConsultationRepository

from .domain_services import (
    ConsultationInitializationService,
    AIScreeningService,
    RecommendationGenerationService,
    UrgencyScoringService
)

__all__ = [
    # Value Objects - Enums
    "ConsultationStatus",
    "MessageType",
    "RecommendationType",
    # Value Objects - IDs
    "ConsultationId",
    "PatientId",
    "ClinicianId",
    # Value Objects - Concepts
    "ConsultationMessage",
    "MedicalBackground",
    "Symptom",
    "SymptomProfile",
    "MedicalRecommendation",
    "KnowledgeGraphNode",
    "VectorSearchResult",
    "ConsultationStats",
    # Entities
    "Consultation",
    "ConversationThread",
    # Events
    "ConsultationInitiated",
    "AwaitingClinicianReview",
    "ConsultationStarted",
    "ConsultationCompleted",
    "ConsultationCancelled",
    "PatientMessageAdded",
    "AIScreeningCompleted",
    "AIQuestionAsked",
    "ClinicianMessageAdded",
    "AIRecommendationGenerated",
    "RecommendationEndorsed",
    "RecommendationRejected",
    "RecommendationsFinalized",
    "UrgentCaseDetected",
    "ConsultationEscalated",
    "PersonalDataRequested",
    # Repository
    "IClinicalConsultationRepository",
    # Domain Services
    "ConsultationInitializationService",
    "AIScreeningService",
    "RecommendationGenerationService",
    "UrgencyScoringService",
]
