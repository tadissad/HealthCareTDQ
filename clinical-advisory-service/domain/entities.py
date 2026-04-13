"""
Clinical-Advisory Service Domain Layer - Entities
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from shared_ddd.base import Entity, Aggregate

from .value_objects import (
    ConsultationId, PatientId, ClinicianId, ConsultationStatus, MessageType,
    ConsultationMessage, MedicalBackground, SymptomProfile, MedicalRecommendation,
    RecommendationType, ConsultationStats
)
from .events import (
    ConsultationInitiated, AwaitingClinicianReview, ConsultationStarted,
    ConsultationCompleted, ConsultationCancelled, PatientMessageAdded,
    AIScreeningCompleted, AIQuestionAsked, ClinicianMessageAdded,
    AIRecommendationGenerated, RecommendationEndorsed, RecommendationRejected,
    RecommendationsFinalized, UrgentCaseDetected, ConsultationEscalated,
    PersonalDataRequested
)


@dataclass
class ConversationThread(Entity):
    """Manages conversation history in consultation"""
    messages: List[ConsultationMessage] = field(default_factory=list)
    
    def add_message(self, message: ConsultationMessage) -> None:
        """Add message to conversation"""
        if not message.content or len(message.content.strip()) < 1:
            raise ValueError("Message content cannot be empty")
        self.messages.append(message)
    
    def get_patient_messages(self) -> List[ConsultationMessage]:
        """Get all messages from patient"""
        return [m for m in self.messages if m.message_type == MessageType.PATIENT_SYMPTOM 
                or m.message_type == MessageType.PATIENT_QUESTION]
    
    def get_ai_messages(self) -> List[ConsultationMessage]:
        """Get all messages from AI"""
        return [m for m in self.messages if "AI_" in m.message_type.value]
    
    def get_clinician_messages(self) -> List[ConsultationMessage]:
        """Get all messages from clinician"""
        return [m for m in self.messages if m.message_type == MessageType.CLINICIAN_ADVICE]
    
    def get_message_count(self, message_type: Optional[MessageType] = None) -> int:
        """Count messages, optionally by type"""
        if message_type:
            return len([m for m in self.messages if m.message_type == message_type])
        return len(self.messages)
    
    def get_average_response_time(self) -> int:
        """Calculate average response time in minutes"""
        if len(self.messages) < 2:
            return 0
        total_time = 0
        for i in range(1, len(self.messages)):
            delta = self.messages[i].timestamp - self.messages[i-1].timestamp
            total_time += int(delta.total_seconds() / 60)
        return total_time // (len(self.messages) - 1)


@dataclass
class Consultation(Aggregate):
    """Consultation aggregate - main DDD entity for clinical advisory"""
    
    # Identity
    consultation_id: ConsultationId
    patient_id: PatientId
    assigned_clinician_id: Optional[ClinicianId] = None
    
    # Medical data
    medical_background: MedicalBackground = field(default_factory=lambda: MedicalBackground(age=0, gender="Other"))
    symptom_profile: SymptomProfile = field(default_factory=lambda: SymptomProfile(symptoms=[], chief_complaint=""))
    
    # Conversation
    conversation: ConversationThread = field(default_factory=ConversationThread)
    
    # Recommendations
    recommendations: List[MedicalRecommendation] = field(default_factory=list)
    
    # Status
    status: ConsultationStatus = ConsultationStatus.INITIATED
    urgency_level: str = "low"  # low, medium, high, urgent
    
    # Timestamps
    initiated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Additional
    notes: Optional[str] = None
    is_urgent: bool = False
    
    def __post_init__(self):
        """Validate consultation on creation"""
        super().__post_init__()
        if not self.consultation_id:
            raise ValueError("Consultation ID is required")
        if not self.patient_id:
            raise ValueError("Patient ID is required")
        # Raise initialization event
        self.add_event(ConsultationInitiated(
            consultation_id=self.consultation_id.value,
            patient_id=self.patient_id.value,
            chief_complaint=self.symptom_profile.chief_complaint,
            symptoms=[{"symptom_name": s.symptom_name, "severity": s.severity} 
                     for s in self.symptom_profile.symptoms],
            medical_background={
                "age": self.medical_background.age,
                "gender": self.medical_background.gender,
                "chronic_conditions": self.medical_background.chronic_conditions
            }
        ))
    
    # ========================================================================
    # Status Management Methods
    # ========================================================================
    
    def start_consultation(self) -> None:
        """Move consultation to IN_PROGRESS status"""
        if self.status != ConsultationStatus.INITIATED:
            raise ValueError(f"Cannot start consultation with status {self.status.value}")
        self.status = ConsultationStatus.IN_PROGRESS
        self.started_at = datetime.now()
        self.add_event(ConsultationStarted(
            consultation_id=self.consultation_id.value,
            started_at=self.started_at
        ))
    
    def request_clinician_review(self, clinician_id: ClinicianId) -> None:
        """Request human clinician review"""
        if self.status in (ConsultationStatus.COMPLETED, ConsultationStatus.CANCELLED):
            raise ValueError(f"Cannot request review for {self.status.value} consultation")
        self.assigned_clinician_id = clinician_id
        self.status = ConsultationStatus.AWAITING_CLINICIAN
        self.add_event(AwaitingClinicianReview(
            consultation_id=self.consultation_id.value,
            assigned_clinician_id=clinician_id.value
        ))
    
    def complete_consultation(self, reason: str = "patient_satisfied") -> None:
        """Mark consultation as completed"""
        if self.status == ConsultationStatus.COMPLETED:
            raise ValueError("Consultation already completed")
        if self.status == ConsultationStatus.CANCELLED:
            raise ValueError("Cannot complete cancelled consultation")
        self.status = ConsultationStatus.COMPLETED
        self.completed_at = datetime.now()
        self.add_event(ConsultationCompleted(
            consultation_id=self.consultation_id.value,
            reason=reason,
            final_recommendations_count=len(self.recommendations),
            completed_at=self.completed_at
        ))
    
    def cancel_consultation(self, reason: str, cancelled_by: str = "patient") -> None:
        """Cancel consultation"""
        if self.status == ConsultationStatus.COMPLETED:
            raise ValueError("Cannot cancel completed consultation")
        if self.status == ConsultationStatus.CANCELLED:
            raise ValueError("Consultation already cancelled")
        self.status = ConsultationStatus.CANCELLED
        self.add_event(ConsultationCancelled(
            consultation_id=self.consultation_id.value,
            cancellation_reason=reason,
            cancelled_by=cancelled_by
        ))
    
    # ========================================================================
    # Conversation Management Methods
    # ========================================================================
    
    def add_patient_message(self, content: str, message_type: MessageType = MessageType.PATIENT_SYMPTOM) -> str:
        """Patient sends message to consultation"""
        if self.status not in (ConsultationStatus.IN_PROGRESS, ConsultationStatus.INITIATED):
            raise ValueError(f"Cannot add message to {self.status.value} consultation")
        
        message = ConsultationMessage(
            message_type=message_type,
            sender_id=self.patient_id.value,
            sender_name="Patient",
            content=content
        )
        self.conversation.add_message(message)
        self.add_event(PatientMessageAdded(
            consultation_id=self.consultation_id.value,
            message_id=message.message_id,
            content=content,
            message_type=message_type.value
        ))
        return message.message_id
    
    def add_ai_message(self, content: str, message_type: MessageType = MessageType.AI_SCREENING,
                       sender_name: str = "AI Assistant") -> str:
        """AI assistant sends message"""
        message = ConsultationMessage(
            message_type=message_type,
            sender_id="ai-system",
            sender_name=sender_name,
            content=content
        )
        self.conversation.add_message(message)
        
        if message_type == MessageType.AI_SCREENING:
            self.add_event(AIScreeningCompleted(
                consultation_id=self.consultation_id.value,
                screening_summary=content
            ))
        elif message_type == MessageType.AI_QUESTION:
            self.add_event(AIQuestionAsked(
                consultation_id=self.consultation_id.value,
                question_id=message.message_id,
                question=content
            ))
        return message.message_id
    
    def add_clinician_message(self, content: str, clinician_id: ClinicianId,
                             advice_type: str = "treatment", sender_name: str = "Dr.") -> str:
        """Clinician adds medical advice"""
        message = ConsultationMessage(
            message_type=MessageType.CLINICIAN_ADVICE,
            sender_id=clinician_id.value,
            sender_name=sender_name,
            content=content
        )
        self.conversation.add_message(message)
        self.add_event(ClinicianMessageAdded(
            consultation_id=self.consultation_id.value,
            clinician_id=clinician_id.value,
            message_id=message.message_id,
            content=content,
            advice_type=advice_type
        ))
        return message.message_id
    
    # ========================================================================
    # Recommendation Management Methods
    # ========================================================================
    
    def add_ai_recommendation(self, recommendation: MedicalRecommendation) -> None:
        """Add AI-generated recommendation"""
        if self.status not in (ConsultationStatus.IN_PROGRESS, ConsultationStatus.RECOMMENDATION_PENDING):
            raise ValueError(f"Cannot add recommendation to {self.status.value} consultation")
        
        self.recommendations.append(recommendation)
        if self.status == ConsultationStatus.IN_PROGRESS:
            self.status = ConsultationStatus.RECOMMENDATION_PENDING
        
        self.add_event(AIRecommendationGenerated(
            consultation_id=self.consultation_id.value,
            recommendation_id=recommendation.recommendation_id,
            recommendation_type=recommendation.recommendation_type.value,
            recommendation_title=recommendation.title,
            description=recommendation.description,
            confidence_score=recommendation.confidence_score,
            requires_clinician_review=not recommendation.clinician_endorsed
        ))
    
    def endorse_recommendation(self, recommendation_id: str, clinician_id: ClinicianId,
                              notes: Optional[str] = None) -> None:
        """Clinician endorses AI recommendation"""
        rec = self._find_recommendation(recommendation_id)
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")
        
        # Create new endorsed recommendation
        endorsed_rec = MedicalRecommendation(
            recommendation_id=rec.recommendation_id,
            recommendation_type=rec.recommendation_type,
            title=rec.title,
            description=rec.description,
            confidence_score=rec.confidence_score,
            clinician_endorsed=True,
            contraindications=rec.contraindications
        )
        
        idx = self.recommendations.index(rec)
        self.recommendations[idx] = endorsed_rec
        
        self.add_event(RecommendationEndorsed(
            consultation_id=self.consultation_id.value,
            recommendation_id=recommendation_id,
            clinician_id=clinician_id.value,
            clinician_notes=notes
        ))
    
    def reject_recommendation(self, recommendation_id: str, clinician_id: ClinicianId,
                              reason: str) -> None:
        """Clinician rejects AI recommendation"""
        rec = self._find_recommendation(recommendation_id)
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")
        
        self.recommendations.remove(rec)
        self.add_event(RecommendationRejected(
            consultation_id=self.consultation_id.value,
            recommendation_id=recommendation_id,
            clinician_id=clinician_id.value,
            rejection_reason=reason
        ))
    
    def finalize_recommendations(self) -> None:
        """Mark recommendations as finalized"""
        if not self.recommendations:
            raise ValueError("No recommendations to finalize")
        
        endorsed_count = sum(1 for r in self.recommendations if r.clinician_endorsed)
        self.status = ConsultationStatus.RECOMMENDATION_READY
        
        self.add_event(RecommendationsFinalized(
            consultation_id=self.consultation_id.value,
            total_recommendations=len(self.recommendations),
            endorsed_recommendations=endorsed_count
        ))
    
    # ========================================================================
    # Emergency/Escalation Methods
    # ========================================================================
    
    def flag_urgent_case(self, indicators: List[str], recommended_action: str) -> None:
        """Detect and flag urgent/emergency case"""
        self.is_urgent = True
        self.urgency_level = "urgent"
        self.add_event(UrgentCaseDetected(
            consultation_id=self.consultation_id.value,
            urgency_indicators=indicators,
            recommended_action=recommended_action
        ))
    
    def escalate_to_clinician(self, clinician_id: ClinicianId, reason: str) -> None:
        """Escalate consultation to human clinician"""
        self.assigned_clinician_id = clinician_id
        self.status = ConsultationStatus.AWAITING_CLINICIAN
        self.add_event(ConsultationEscalated(
            consultation_id=self.consultation_id.value,
            escalation_reason=reason,
            assigned_to_clinician_id=clinician_id.value
        ))
    
    def request_additional_data(self, field_names: List[str]) -> None:
        """Request additional patient information"""
        self.add_event(PersonalDataRequested(
            consultation_id=self.consultation_id.value,
            field_names=field_names
        ))
    
    # ========================================================================
    # Query Methods
    # ========================================================================
    
    def get_statistics(self) -> ConsultationStats:
        """Get consultation statistics"""
        return ConsultationStats(
            total_messages=self.conversation.get_message_count(),
            patient_messages=self.conversation.get_message_count(MessageType.PATIENT_SYMPTOM),
            ai_messages=len(self.conversation.get_ai_messages()),
            clinician_messages=len(self.conversation.get_clinician_messages()),
            recommendations_count=len(self.recommendations),
            average_response_time_minutes=self.conversation.get_average_response_time(),
            total_duration_minutes=int((datetime.now() - self.initiated_at).total_seconds() / 60) if self.started_at else 0
        )
    
    def get_endorsed_recommendations(self) -> List[MedicalRecommendation]:
        """Get recommendations endorsed by clinician"""
        return [r for r in self.recommendations if r.clinician_endorsed]
    
    def has_unreviewed_recommendations(self) -> bool:
        """Check if there are unreviewed AI recommendations"""
        return any(not r.clinician_endorsed for r in self.recommendations)
    
    def is_completed(self) -> bool:
        """Check if consultation is completed"""
        return self.status == ConsultationStatus.COMPLETED
    
    def is_active(self) -> bool:
        """Check if consultation is still active"""
        return self.status in (ConsultationStatus.IN_PROGRESS, ConsultationStatus.RECOMMENDATION_PENDING,
                               ConsultationStatus.AWAITING_CLINICIAN)
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _find_recommendation(self, recommendation_id: str) -> Optional[MedicalRecommendation]:
        """Find recommendation by ID"""
        for rec in self.recommendations:
            if rec.recommendation_id == recommendation_id:
                return rec
        return None
