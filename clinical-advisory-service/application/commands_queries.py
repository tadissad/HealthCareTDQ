"""
Clinical-Advisory Service Application Layer - Commands & Queries
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


# ============================================================================
# Command DTOs
# ============================================================================

@dataclass
class InitiateConsultationCommand:
    """Start new consultation"""
    patient_id: str
    chief_complaint: str
    symptoms: List[dict]  # [{"symptom_name": "...", "severity": 8, "duration": "3 days"}]
    age: int
    gender: str
    chronic_conditions: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    current_medications: List[str] = field(default_factory=list)


@dataclass
class AddPatientMessageCommand:
    """Patient sends message to consultation"""
    consultation_id: str
    content: str
    message_type: str = "PATIENT_SYMPTOM"  # or "PATIENT_QUESTION"


@dataclass
class PerformAIScreeningCommand:
    """Trigger AI initial symptom screening"""
    consultation_id: str


@dataclass
class AddAIRecommendationCommand:
    """Add AI-generated recommendation"""
    consultation_id: str
    recommendation_type: str  # SELF_CARE, OTC_MEDICATION, SPECIALIST_REFERRAL, etc
    title: str
    description: str
    confidence_score: float = 0.85
    contraindications: List[str] = field(default_factory=list)


@dataclass
class RequestClinicianReviewCommand:
    """Request human clinician review"""
    consultation_id: str
    clinician_id: str


@dataclass
class EndorseRecommendationCommand:
    """Clinician endorses AI recommendation"""
    consultation_id: str
    recommendation_id: str
    clinician_id: str
    notes: Optional[str] = None


@dataclass
class RejectRecommendationCommand:
    """Clinician rejects AI recommendation"""
    consultation_id: str
    recommendation_id: str
    clinician_id: str
    reason: str


@dataclass
class FinalizeRecommendationsCommand:
    """Finalize all recommendations"""
    consultation_id: str


@dataclass
class CompleteConsultationCommand:
    """Complete consultation"""
    consultation_id: str
    reason: str = "patient_satisfied"


@dataclass
class CancelConsultationCommand:
    """Cancel consultation"""
    consultation_id: str
    reason: str
    cancelled_by: str = "patient"


@dataclass
class EscalateUrgentCaseCommand:
    """Escalate urgent case to clinician"""
    consultation_id: str
    clinician_id: str
    urgency_level: str
    indicators: List[str]


# ============================================================================
# Query DTOs
# ============================================================================

@dataclass
class GetConsultationByIdQuery:
    """Get consultation details"""
    consultation_id: str


@dataclass
class GetPatientConsultationsQuery:
    """Get all consultations for patient"""
    patient_id: str
    limit: int = 20
    offset: int = 0


@dataclass
class ListActiveConsultationsQuery:
    """List all active consultations system-wide"""
    limit: int = 20
    offset: int = 0


@dataclass
class ListPendingClinicianReviewQuery:
    """List consultations awaiting clinician review"""
    limit: int = 20
    offset: int = 0


@dataclass
class ListUrgentCasesQuery:
    """List all urgent/emergency cases"""
    limit: int = 20
    offset: int = 0


@dataclass
class GetConsultationMessagesQuery:
    """Get conversation messages for consultation"""
    consultation_id: str
    message_type: Optional[str] = None  # Filter by type
    limit: int = 50
    offset: int = 0


@dataclass
class GetRecommendationsQuery:
    """Get recommendations for consultation"""
    consultation_id: str
    endorsed_only: bool = False


@dataclass
class GetConsultationStatsQuery:
    """Get consultation statistics"""
    consultation_id: str


@dataclass
class SearchConsultationsQuery:
    """Search consultations by patient ID and status"""
    patient_id: Optional[str] = None
    status: Optional[str] = None
    urgency_level: Optional[str] = None
    limit: int = 20
    offset: int = 0


# ============================================================================
# Result DTOs
# ============================================================================

@dataclass
class ConsultationInitiatedResult:
    """Result of consultation initialization"""
    consultation_id: str
    patient_id: str
    status: str
    created_at: datetime


@dataclass
class MessageAddedResult:
    """Result of adding message"""
    consultation_id: str
    message_id: str
    message_type: str
    added_at: datetime


@dataclass
class ScreeningCompletedResult:
    """Result of AI screening"""
    consultation_id: str
    screening_summary: str
    risk_level: str
    completed_at: datetime


@dataclass
class RecommendationAddedResult:
    """Result of adding recommendation"""
    consultation_id: str
    recommendation_id: str
    recommendation_type: str
    confidence_score: float


@dataclass
class ConsultationActionResult:
    """Generic result for consultation actions"""
    consultation_id: str
    action: str
    old_status: Optional[str]
    new_status: str
    timestamp: datetime


# ============================================================================
# DTO Classes for Responses
# ============================================================================

@dataclass
class MessageDTO:
    """Message data"""
    message_id: str
    message_type: str
    sender_id: str
    sender_name: str
    content: str
    timestamp: datetime


@dataclass
class RecommendationDTO:
    """Recommendation data"""
    recommendation_id: str
    recommendation_type: str
    title: str
    description: str
    confidence_score: float
    clinician_endorsed: bool
    contraindications: List[str]
    created_at: datetime


@dataclass
class ConsultationDetailDTO:
    """Detailed consultation information"""
    consultation_id: str
    patient_id: str
    status: str
    urgency_level: str
    chief_complaint: str
    symptoms: List[dict]
    medical_background: dict
    messages: List[MessageDTO]
    recommendations: List[RecommendationDTO]
    initiated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


@dataclass
class ConsultationSummaryDTO:
    """Summary consultation information"""
    consultation_id: str
    patient_id: str
    status: str
    chief_complaint: str
    urgency_level: str
    message_count: int
    recommendation_count: int
    initiated_at: datetime
    is_active: bool


@dataclass
class ConsultationListDTO:
    """List of consultations with pagination"""
    items: List[ConsultationSummaryDTO]
    total_count: int
    limit: int
    offset: int
