"""
Clinical-Advisory Service Domain Layer - Value Objects
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid


# ============================================================================
# Enums
# ============================================================================

class ConsultationStatus(Enum):
    """Consultation lifecycle status"""
    INITIATED = "INITIATED"           # Patient just started
    AWAITING_CLINICIAN = "AWAITING_CLINICIAN"  # Looking for AI/clinician
    IN_PROGRESS = "IN_PROGRESS"      # Active conversation
    RECOMMENDATION_PENDING = "RECOMMENDATION_PENDING"  # Waiting for AI rec
    RECOMMENDATION_READY = "RECOMMENDATION_READY"    # AI recommendations available
    COMPLETED = "COMPLETED"          # Patient satisfied, closed
    CANCELLED = "CANCELLED"          # Abandoned/cancelled


class MessageType(Enum):
    """Types of messages in consultation thread"""
    PATIENT_SYMPTOM = "PATIENT_SYMPTOM"      # Patient describing symptoms
    PATIENT_QUESTION = "PATIENT_QUESTION"    # Patient asking question
    AI_SCREENING = "AI_SCREENING"            # AI initial screening
    AI_QUESTION = "AI_QUESTION"              # AI asking clarifying questions
    AI_RECOMMENDATION = "AI_RECOMMENDATION"  # AI medical recommendations
    CLINICIAN_ADVICE = "CLINICIAN_ADVICE"   # Licensed clinician response
    SYSTEM_NOTE = "SYSTEM_NOTE"              # System messages


class RecommendationType(Enum):
    """Types of AI recommendations"""
    SELF_CARE = "SELF_CARE"              # Home remedies, lifestyle changes
    OTC_MEDICATION = "OTC_MEDICATION"    # Over-the-counter medication
    SPECIALIST_REFERRAL = "SPECIALIST_REFERRAL"  # Refer to specialist
    URGENT_CARE = "URGENT_CARE"          # Needs immediate attention
    CONDITION_INFO = "CONDITION_INFO"    # Educational about condition


# ============================================================================
# Simple Value Objects
# ============================================================================

@dataclass(frozen=True)
class ConsultationId:
    """Unique consultation identifier"""
    value: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        if not self.value or len(self.value) < 1:
            raise ValueError("Consultation ID cannot be empty")


@dataclass(frozen=True)
class PatientId:
    """Patient identifier"""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Patient ID cannot be empty")


@dataclass(frozen=True)
class ClinicianId:
    """Clinician/specialist identifier"""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Clinician ID cannot be empty")


@dataclass(frozen=True)
class ConsultationMessage:
    """Single message in consultation thread"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.PATIENT_SYMPTOM
    sender_id: str = ""  # Patient ID, clinician ID, or "AI"
    sender_name: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.content or len(self.content.strip()) < 1:
            raise ValueError("Message content cannot be empty")
        if not self.sender_id:
            raise ValueError("Sender ID is required")


@dataclass(frozen=True)
class MedicalBackground:
    """Patient's medical history summary"""
    age: int  # 0-150
    gender: str  # "M", "F", "Other"
    blood_type: Optional[str] = None  # "O+", "A-", etc
    chronic_conditions: List[str] = field(default_factory=list)  # ICD-10 codes
    allergies: List[str] = field(default_factory=list)
    current_medications: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not (0 <= self.age <= 150):
            raise ValueError("Age must be between 0 and 150")
        if self.gender not in ("M", "F", "Other"):
            raise ValueError("Invalid gender")


@dataclass(frozen=True)
class Symptom:
    """Single patient symptom"""
    symptom_name: str  # e.g., "Headache", "Fever"
    duration: str  # e.g., "3 days", "1 week"
    severity: int  # 1-10
    description: Optional[str] = None
    
    def __post_init__(self):
        if not self.symptom_name:
            raise ValueError("Symptom name is required")
        if not (1 <= self.severity <= 10):
            raise ValueError("Severity must be between 1 and 10")


@dataclass(frozen=True)
class SymptomProfile:
    """Collection of patient's current symptoms"""
    symptoms: List[Symptom] = field(default_factory=list)
    onset_date: datetime = field(default_factory=datetime.now)
    chief_complaint: str = ""  # Main symptom bringing patient in
    
    def __post_init__(self):
        if len(self.symptoms) == 0:
            raise ValueError("At least one symptom must be provided")
        if not self.chief_complaint:
            raise ValueError("Chief complaint is required")


@dataclass(frozen=True)
class MedicalRecommendation:
    """AI or clinician recommendation"""
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_type: RecommendationType = RecommendationType.SELF_CARE
    title: str = ""
    description: str = ""
    contraindications: List[str] = field(default_factory=list)
    confidence_score: float = 0.0  # 0-1 for AI confidence
    clinician_endorsed: bool = False  # Validated by licensed clinician
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.title:
            raise ValueError("Recommendation title is required")
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0 and 1")


@dataclass(frozen=True)
class KnowledgeGraphNode:
    """Node in medical knowledge graph"""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: str = ""  # "condition", "symptom", "treatment", "medicine"
    medical_code: str = ""  # ICD-10, RxNorm, SNOMED, etc
    name: str = ""
    description: str = ""
    relationships: List[str] = field(default_factory=list)  # IDs of related nodes
    
    def __post_init__(self):
        if not self.node_type:
            raise ValueError("Node type is required")
        if not self.name:
            raise ValueError("Node name is required")


@dataclass(frozen=True)
class VectorSearchResult:
    """Result from FAISS semantic search"""
    result_id: str
    result_type: str  # "condition", "recommendation", "medicine"
    name: str
    similarity_score: float  # 0-1
    metadata: dict = field(default_factory=dict)


# ============================================================================
# Status DTOs
# ============================================================================

@dataclass(frozen=True)
class ConsultationStats:
    """Statistics about consultation"""
    total_messages: int = 0
    patient_messages: int = 0
    ai_messages: int = 0
    clinician_messages: int = 0
    recommendations_count: int = 0
    average_response_time_minutes: int = 0
    total_duration_minutes: int = 0
