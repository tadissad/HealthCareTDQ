"""
Clinical-Advisory Service Domain Layer - Domain Events
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from shared_ddd.base import DomainEvent


# ============================================================================
# Consultation Lifecycle Events
# ============================================================================

@dataclass
class ConsultationInitiated(DomainEvent):
    """Consultation started by patient"""
    consultation_id: str
    patient_id: str
    chief_complaint: str
    symptoms: List[dict]  # [{"symptom_name": "...", "severity": 8, ...}]
    medical_background: dict  # {"age": 45, "gender": "M", ...}
    event_type: str = "ConsultationInitiated"


@dataclass
class AwaitingClinicianReview(DomainEvent):
    """Consultation moved to awaiting clinician"""
    consultation_id: str
    assigned_clinician_id: Optional[str] = None
    event_type: str = "AwaitingClinicianReview"


@dataclass
class ConsultationStarted(DomainEvent):
    """Consultation transitioned to in-progress"""
    consultation_id: str
    ai_consultant_id: str = "ai-system"
    started_at: datetime = field(default_factory=datetime.now)
    event_type: str = "ConsultationStarted"


@dataclass
class ConsultationCompleted(DomainEvent):
    """Consultation successfully completed"""
    consultation_id: str
    reason: str = "patient_satisfied"
    final_recommendations_count: int = 0
    completed_at: datetime = field(default_factory=datetime.now)
    event_type: str = "ConsultationCompleted"


@dataclass
class ConsultationCancelled(DomainEvent):
    """Consultation cancelled"""
    consultation_id: str
    cancellation_reason: str
    cancelled_by: str  # "patient" or "system"
    cancelled_at: datetime = field(default_factory=datetime.now)
    event_type: str = "ConsultationCancelled"


# ============================================================================
# Message Events
# ============================================================================

@dataclass
class PatientMessageAdded(DomainEvent):
    """Patient sent message to consultation"""
    consultation_id: str
    message_id: str
    content: str
    message_type: str  # "SYMPTOM", "QUESTION", "UPDATE"
    added_at: datetime = field(default_factory=datetime.now)
    event_type: str = "PatientMessageAdded"


@dataclass
class AIScreeningCompleted(DomainEvent):
    """AI completed initial symptom screening"""
    consultation_id: str
    screening_summary: str
    questions_for_patient: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high, urgent
    completed_at: datetime = field(default_factory=datetime.now)
    event_type: str = "AIScreeningCompleted"


@dataclass
class AIQuestionAsked(DomainEvent):
    """AI asking clarifying question"""
    consultation_id: str
    question_id: str
    question: str
    question_category: str  # "symptoms", "medical_history", "lifestyle"
    asked_at: datetime = field(default_factory=datetime.now)
    event_type: str = "AIQuestionAsked"


@dataclass
class ClinicianMessageAdded(DomainEvent):
    """Clinician added medical advice"""
    consultation_id: str
    clinician_id: str
    message_id: str
    content: str
    advice_type: str  # "treatment", "referral", "education"
    added_at: datetime = field(default_factory=datetime.now)
    event_type: str = "ClinicianMessageAdded"


# ============================================================================
# Recommendation Events
# ============================================================================

@dataclass
class AIRecommendationGenerated(DomainEvent):
    """AI generated clinical recommendation"""
    consultation_id: str
    recommendation_id: str
    recommendation_type: str  # SELF_CARE, OTC_MEDICATION, SPECIALIST_REFERRAL, etc
    recommendation_title: str
    description: str
    confidence_score: float
    requires_clinician_review: bool
    generated_at: datetime = field(default_factory=datetime.now)
    event_type: str = "AIRecommendationGenerated"


@dataclass
class RecommendationEndorsed(DomainEvent):
    """Clinician endorsed AI recommendation"""
    consultation_id: str
    recommendation_id: str
    clinician_id: str
    clinician_notes: Optional[str] = None
    endorsed_at: datetime = field(default_factory=datetime.now)
    event_type: str = "RecommendationEndorsed"


@dataclass
class RecommendationRejected(DomainEvent):
    """Clinician rejected AI recommendation"""
    consultation_id: str
    recommendation_id: str
    clinician_id: str
    rejection_reason: str
    rejected_at: datetime = field(default_factory=datetime.now)
    event_type: str = "RecommendationRejected"


@dataclass
class RecommendationsFinalized(DomainEvent):
    """All recommendations finalized for consultation"""
    consultation_id: str
    total_recommendations: int
    endorsed_recommendations: int
    finalized_at: datetime = field(default_factory=datetime.now)
    event_type: str = "RecommendationsFinalized"


# ============================================================================
# Knowledge Graph Events
# ============================================================================

@dataclass
class KnowledgeGraphSearchExecuted(DomainEvent):
    """Semantic search executed on medical knowledge graph"""
    consultation_id: str
    query: str
    results_count: int
    top_result_type: str
    executed_at: datetime = field(default_factory=datetime.now)
    event_type: str = "KnowledgeGraphSearchExecuted"


@dataclass
class VectorSearchExecuted(DomainEvent):
    """FAISS vector similarity search executed"""
    consultation_id: str
    query_embedding: str  # Could store embedding ID or summary
    results_count: int
    average_similarity: float
    executed_at: datetime = field(default_factory=datetime.now)
    event_type: str = "VectorSearchExecuted"


# ============================================================================
# Error/Escalation Events
# ============================================================================

@dataclass
class UrgentCaseDetected(DomainEvent):
    """AI detected urgent/emergency case"""
    consultation_id: str
    urgency_indicators: List[str]  # ["high_fever", "chest_pain", ...]
    recommended_action: str  # "call_ambulance", "emergency_room", "urgent_care"
    detected_at: datetime = field(default_factory=datetime.now)
    event_type: str = "UrgentCaseDetected"


@dataclass
class ConsultationEscalated(DomainEvent):
    """Consultation escalated to human clinician"""
    consultation_id: str
    escalation_reason: str
    assigned_to_clinician_id: str
    escalated_at: datetime = field(default_factory=datetime.now)
    event_type: str = "ConsultationEscalated"


@dataclass
class PersonalDataRequested(DomainEvent):
    """Additional patient information needed"""
    consultation_id: str
    field_names: List[str]  # ["medical_history", "allergies", ...]
    requested_at: datetime = field(default_factory=datetime.now)
    event_type: str = "PersonalDataRequested"
