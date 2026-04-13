"""
Clinical-Advisory Service Application Layer - Handlers
"""

from typing import Optional
from datetime import datetime

from clinical_advisory_service.domain import (
    Consultation, PatientId, ClinicianId, ConsultationId,
    Symptom, SymptomProfile, MedicalBackground,
    ConsultationInitializationService, AIScreeningService,
    RecommendationGenerationService, UrgencyScoringService,
    IClinicalConsultationRepository
)
from .commands_queries import (
    # Commands
    InitiateConsultationCommand, AddPatientMessageCommand,
    PerformAIScreeningCommand, AddAIRecommendationCommand,
    RequestClinicianReviewCommand, EndorseRecommendationCommand,
    RejectRecommendationCommand, FinalizeRecommendationsCommand,
    CompleteConsultationCommand, CancelConsultationCommand,
    EscalateUrgentCaseCommand,
    # Query Classes
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


# ============================================================================
# Command Handlers
# ============================================================================

class InitiateConsultationHandler:
    """Handle consultation initiation"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
        self.init_service = ConsultationInitializationService()
    
    def handle(self, command: InitiateConsultationCommand) -> ConsultationInitiatedResult:
        """Initiate new consultation"""
        patient_id = PatientId(command.patient_id)
        
        # Create symptoms
        symptoms = [
            Symptom(
                symptom_name=s['symptom_name'],
                duration=s['duration'],
                severity=s['severity'],
                description=s.get('description')
            )
            for s in command.symptoms
        ]
        
        # Create medical background
        background = MedicalBackground(
            age=command.age,
            gender=command.gender,
            chronic_conditions=command.chronic_conditions,
            allergies=command.allergies,
            current_medications=command.current_medications
        )
        
        # Use domain service to create consultation
        consultation = self.init_service.create_consultation(
            patient_id=patient_id,
            chief_complaint=command.chief_complaint,
            symptoms=symptoms,
            medical_background=background
        )
        
        # Persist
        self.repository.add(consultation)
        
        return ConsultationInitiatedResult(
            consultation_id=consultation.consultation_id.value,
            patient_id=command.patient_id,
            status="INITIATED",
            created_at=datetime.now()
        )


class AddPatientMessageHandler:
    """Handle adding patient message"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
    
    def handle(self, command: AddPatientMessageCommand) -> MessageAddedResult:
        """Add patient message to consultation"""
        consultation = self.repository.get_by_id(ConsultationId(command.consultation_id))
        if not consultation:
            raise ValueError(f"Consultation {command.consultation_id} not found")
        
        message_id = consultation.add_patient_message(command.content)
        self.repository.update(consultation)
        
        return MessageAddedResult(
            consultation_id=command.consultation_id,
            message_id=message_id,
            message_type=command.message_type,
            added_at=datetime.now()
        )


class PerformAIScreeningHandler:
    """Handle AI screening"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
        self.screening_service = AIScreeningService()
    
    def handle(self, command: PerformAIScreeningCommand) -> ScreeningCompletedResult:
        """Perform AI initial symptom screening"""
        consultation = self.repository.get_by_id(ConsultationId(command.consultation_id))
        if not consultation:
            raise ValueError(f"Consultation {command.consultation_id} not found")
        
        screening_summary = self.screening_service.perform_initial_screening(consultation)
        self.repository.update(consultation)
        
        return ScreeningCompletedResult(
            consultation_id=command.consultation_id,
            screening_summary=screening_summary,
            risk_level="low",  # Will be determined by UrgencyScoringService
            completed_at=datetime.now()
        )


class AddAIRecommendationHandler:
    """Handle adding AI recommendation"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
        self.rec_service = RecommendationGenerationService()
    
    def handle(self, command: AddAIRecommendationCommand) -> RecommendationAddedResult:
        """Add AI-generated recommendation"""
        consultation = self.repository.get_by_id(ConsultationId(command.consultation_id))
        if not consultation:
            raise ValueError(f"Consultation {command.consultation_id} not found")
        
        # Create recommendation based on type
        recommendation = self.rec_service.generate_self_care_recommendation(
            title=command.title,
            description=command.description,
            confidence_score=command.confidence_score,
            contraindications=command.contraindications
        )
        
        consultation.add_ai_recommendation(recommendation)
        self.repository.update(consultation)
        
        return RecommendationAddedResult(
            consultation_id=command.consultation_id,
            recommendation_id=recommendation.recommendation_id,
            recommendation_type=recommendation.recommendation_type.value,
            confidence_score=recommendation.confidence_score
        )


class EndorseRecommendationHandler:
    """Handle clinician endorsing recommendation"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
    
    def handle(self, command: EndorseRecommendationCommand) -> ConsultationActionResult:
        """Endorse recommendation"""
        consultation = self.repository.get_by_id(ConsultationId(command.consultation_id))
        if not consultation:
            raise ValueError(f"Consultation {command.consultation_id} not found")
        
        clinician_id = ClinicianId(command.clinician_id)
        consultation.endorse_recommendation(
            command.recommendation_id,
            clinician_id,
            command.notes
        )
        self.repository.update(consultation)
        
        return ConsultationActionResult(
            consultation_id=command.consultation_id,
            action="endorse_recommendation",
            old_status=None,
            new_status="recommendation_endorsed",
            timestamp=datetime.now()
        )


class RequestClinicianReviewHandler:
    """Handle requesting clinician review"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
    
    def handle(self, command: RequestClinicianReviewCommand) -> ConsultationActionResult:
        """Request clinician review"""
        consultation = self.repository.get_by_id(ConsultationId(command.consultation_id))
        if not consultation:
            raise ValueError(f"Consultation {command.consultation_id} not found")
        
        old_status = consultation.status.value
        clinician_id = ClinicianId(command.clinician_id)
        consultation.request_clinician_review(clinician_id)
        self.repository.update(consultation)
        
        return ConsultationActionResult(
            consultation_id=command.consultation_id,
            action="request_clinician_review",
            old_status=old_status,
            new_status=consultation.status.value,
            timestamp=datetime.now()
        )


class CompleteConsultationHandler:
    """Handle consultation completion"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
    
    def handle(self, command: CompleteConsultationCommand) -> ConsultationActionResult:
        """Complete consultation"""
        consultation = self.repository.get_by_id(ConsultationId(command.consultation_id))
        if not consultation:
            raise ValueError(f"Consultation {command.consultation_id} not found")
        
        old_status = consultation.status.value
        consultation.complete_consultation(command.reason)
        self.repository.update(consultation)
        
        return ConsultationActionResult(
            consultation_id=command.consultation_id,
            action="complete_consultation",
            old_status=old_status,
            new_status=consultation.status.value,
            timestamp=datetime.now()
        )


class EscalateUrgentCaseHandler:
    """Handle escalating urgent case"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
    
    def handle(self, command: EscalateUrgentCaseCommand) -> ConsultationActionResult:
        """Escalate urgent case to clinician"""
        consultation = self.repository.get_by_id(ConsultationId(command.consultation_id))
        if not consultation:
            raise ValueError(f"Consultation {command.consultation_id} not found")
        
        old_status = consultation.status.value
        consultation.flag_urgent_case(command.indicators, command.urgency_level)
        clinician_id = ClinicianId(command.clinician_id)
        consultation.escalate_to_clinician(clinician_id, "Urgent case detected")
        self.repository.update(consultation)
        
        return ConsultationActionResult(
            consultation_id=command.consultation_id,
            action="escalate_urgent_case",
            old_status=old_status,
            new_status=consultation.status.value,
            timestamp=datetime.now()
        )


# ============================================================================
# Query Handlers
# ============================================================================

class GetConsultationByIdHandler:
    """Get consultation by ID"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
    
    def handle(self, query: GetConsultationByIdQuery) -> Optional[ConsultationDetailDTO]:
        """Get consultation details"""
        consultation = self.repository.get_by_id(ConsultationId(query.consultation_id))
        if not consultation:
            return None
        
        return self._map_to_detail_dto(consultation)
    
    @staticmethod
    def _map_to_detail_dto(consultation: Consultation) -> ConsultationDetailDTO:
        """Map entity to detail DTO"""
        messages = [
            MessageDTO(
                message_id=msg.message_id,
                message_type=msg.message_type.value,
                sender_id=msg.sender_id,
                sender_name=msg.sender_name,
                content=msg.content,
                timestamp=msg.timestamp
            )
            for msg in consultation.conversation.messages
        ]
        
        recommendations = [
            RecommendationDTO(
                recommendation_id=r.recommendation_id,
                recommendation_type=r.recommendation_type.value,
                title=r.title,
                description=r.description,
                confidence_score=r.confidence_score,
                clinician_endorsed=r.clinician_endorsed,
                contraindications=r.contraindications,
                created_at=r.created_at
            )
            for r in consultation.recommendations
        ]
        
        return ConsultationDetailDTO(
            consultation_id=consultation.consultation_id.value,
            patient_id=consultation.patient_id.value,
            status=consultation.status.value,
            urgency_level=consultation.urgency_level,
            chief_complaint=consultation.symptom_profile.chief_complaint,
            symptoms=[{
                "name": s.symptom_name,
                "severity": s.severity,
                "duration": s.duration
            } for s in consultation.symptom_profile.symptoms],
            medical_background={
                "age": consultation.medical_background.age,
                "gender": consultation.medical_background.gender,
                "chronic_conditions": consultation.medical_background.chronic_conditions,
                "allergies": consultation.medical_background.allergies
            },
            messages=messages,
            recommendations=recommendations,
            initiated_at=consultation.initiated_at,
            started_at=consultation.started_at,
            completed_at=consultation.completed_at
        )


class GetPatientConsultationsHandler:
    """Get consultations for patient"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
    
    def handle(self, query: GetPatientConsultationsQuery) -> ConsultationListDTO:
        """Get patient consultations"""
        consultations = self.repository.get_by_patient_id(PatientId(query.patient_id))
        
        total = len(consultations)
        items = consultations[query.offset:query.offset + query.limit]
        
        summaries = [self._map_to_summary(c) for c in items]
        
        return ConsultationListDTO(
            items=summaries,
            total_count=total,
            limit=query.limit,
            offset=query.offset
        )
    
    @staticmethod
    def _map_to_summary(consultation: Consultation) -> ConsultationSummaryDTO:
        """Map to summary DTO"""
        return ConsultationSummaryDTO(
            consultation_id=consultation.consultation_id.value,
            patient_id=consultation.patient_id.value,
            status=consultation.status.value,
            chief_complaint=consultation.symptom_profile.chief_complaint,
            urgency_level=consultation.urgency_level,
            message_count=len(consultation.conversation.messages),
            recommendation_count=len(consultation.recommendations),
            initiated_at=consultation.initiated_at,
            is_active=consultation.is_active()
        )


class ListActiveConsultationsHandler:
    """List active consultations system-wide"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
    
    def handle(self, query: ListActiveConsultationsQuery) -> ConsultationListDTO:
        """List active consultations"""
        consultations = self.repository.list_active_consultations()
        
        total = len(consultations)
        items = consultations[query.offset:query.offset + query.limit]
        
        summaries = [self._map_to_summary(c) for c in items]
        
        return ConsultationListDTO(
            items=summaries,
            total_count=total,
            limit=query.limit,
            offset=query.offset
        )
    
    @staticmethod
    def _map_to_summary(consultation: Consultation) -> ConsultationSummaryDTO:
        """Map to summary DTO"""
        return ConsultationSummaryDTO(
            consultation_id=consultation.consultation_id.value,
            patient_id=consultation.patient_id.value,
            status=consultation.status.value,
            chief_complaint=consultation.symptom_profile.chief_complaint,
            urgency_level=consultation.urgency_level,
            message_count=len(consultation.conversation.messages),
            recommendation_count=len(consultation.recommendations),
            initiated_at=consultation.initiated_at,
            is_active=True
        )


class ListUrgentCasesHandler:
    """List urgent cases"""
    
    def __init__(self, repository: IClinicalConsultationRepository):
        self.repository = repository
    
    def handle(self, query: ListUrgentCasesQuery) -> ConsultationListDTO:
        """List urgent cases"""
        consultations = self.repository.list_urgent_cases()
        
        total = len(consultations)
        items = consultations[query.offset:query.offset + query.limit]
        
        summaries = [self._map_to_summary(c) for c in items]
        
        return ConsultationListDTO(
            items=summaries,
            total_count=total,
            limit=query.limit,
            offset=query.offset
        )
    
    @staticmethod
    def _map_to_summary(consultation: Consultation) -> ConsultationSummaryDTO:
        """Map to summary DTO"""
        return ConsultationSummaryDTO(
            consultation_id=consultation.consultation_id.value,
            patient_id=consultation.patient_id.value,
            status=consultation.status.value,
            chief_complaint=consultation.symptom_profile.chief_complaint,
            urgency_level=consultation.urgency_level,
            message_count=len(consultation.conversation.messages),
            recommendation_count=len(consultation.recommendations),
            initiated_at=consultation.initiated_at,
            is_active=consultation.is_active()
        )
