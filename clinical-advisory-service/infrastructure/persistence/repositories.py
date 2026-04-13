"""
Clinical-Advisory Service - Infrastructure Layer - Repositories
Repository implementations mapping domain entities to ORM models
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from clinical_advisory_service.domain.repositories import IClinicalConsultationRepository
from clinical_advisory_service.domain.entities import Consultation, ConversationThread
from clinical_advisory_service.domain.value_objects import (
    ConsultationId, PatientId, ClinicianId, MedicalBackground, Symptom,
    SymptomProfile
)
from clinical_advisory_service.infrastructure.persistence.models import (
    ConsultationModel, ConsultationMessageModel, ConsultationRecommendationModel,
    DomainEventModel
)
from shared_ddd.event_bus import EventBusFactory
import json

logger = logging.getLogger(__name__)


class ConsultationRepositoryImpl(IClinicalConsultationRepository):
    """Repository implementation for Consultation aggregate"""
    
    def save(self, consultation: Consultation) -> None:
        """Save consultation aggregate to database"""
        try:
            # Map domain entity to ORM model
            model_data = {
                'consultation_id': consultation.consultation_id.value,
                'patient_id': consultation.patient_id.value,
                'chief_complaint': consultation.chief_complaint,
                'medical_background_json': consultation.medical_background.to_dict(),
                'urgency_level': consultation.urgency_level,
                'status': consultation._status,
                'is_urgent_case': consultation._is_urgent_case,
                'red_flags_detected': consultation._red_flags_detected,
                'patient_message_count': consultation.message_count.get('PATIENT', 0),
                'ai_message_count': consultation.message_count.get('AI', 0),
                'clinician_message_count': consultation.message_count.get('CLINICIAN', 0),
                'ai_recommendation_count': len([r for r in consultation.recommendations if r.type == 'AI']),
                'endorsed_recommendations_count': len([r for r in consultation.recommendations if r.endorsed]),
                'rejected_recommendations_count': len([r for r in consultation.recommendations if r.rejected]),
            }
            
            if consultation.activated_clinician_id:
                model_data['activated_clinician_id'] = consultation.activated_clinician_id.value
            
            if consultation.completed_at:
                model_data['completed_at'] = consultation.completed_at
            
            if consultation.expires_at:
                model_data['expires_at'] = consultation.expires_at
            
            # Upsert model
            model, created = ConsultationModel.objects.update_or_create(
                consultation_id=consultation.consultation_id.value,
                defaults=model_data
            )
            
            # Extract and publish domain events
            self._publish_domain_events(consultation)
            
            logger.info(f"Consultation saved: {consultation.consultation_id.value} (created: {created})")
            
        except Exception as e:
            logger.error(f"Error saving consultation: {e}")
            raise
    
    def get_by_id(self, consultation_id: ConsultationId) -> Optional[Consultation]:
        """Retrieve consultation by ID"""
        try:
            model = ConsultationModel.objects.get(consultation_id=consultation_id.value)
            return self._model_to_entity(model)
        except ConsultationModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error retrieving consultation: {e}")
            return None
    
    def get_by_patient_id(self, patient_id: PatientId, limit: int = 10) -> List[Consultation]:
        """Get all consultations for a patient"""
        try:
            models = ConsultationModel.objects.filter(
                patient_id=patient_id.value
            ).order_by('-initiated_at')[:limit]
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error retrieving consultations for patient: {e}")
            return []
    
    def get_active_consultations(self, limit: int = 50) -> List[Consultation]:
        """Get all active consultations (not completed or cancelled)"""
        try:
            active_statuses = ['INITIATED', 'AWAITING_CLINICIAN', 'IN_PROGRESS',
                             'RECOMMENDATION_PENDING', 'RECOMMENDATION_READY']
            
            models = ConsultationModel.objects.filter(
                status__in=active_statuses
            ).order_by('-initiated_at')[:limit]
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error retrieving active consultations: {e}")
            return []
    
    def get_urgent_consultations(self, limit: int = 50) -> List[Consultation]:
        """Get all urgent cases pending attention"""
        try:
            models = ConsultationModel.objects.filter(
                is_urgent_case=True,
                status__in=['INITIATED', 'AWAITING_CLINICIAN', 'IN_PROGRESS']
            ).order_by('-initiated_at')[:limit]
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error retrieving urgent consultations: {e}")
            return []
    
    def get_pending_clinician_review(self, limit: int = 50) -> List[Consultation]:
        """Get consultations awaiting clinician review"""
        try:
            models = ConsultationModel.objects.filter(
                status='AWAITING_CLINICIAN'
            ).order_by('initiated_at')[:limit]
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error retrieving pending reviews: {e}")
            return []
    
    def search_consultations(self, query: str, limit: int = 20) -> List[Consultation]:
        """Search consultations by chief complaint"""
        try:
            models = ConsultationModel.objects.filter(
                chief_complaint__icontains=query
            ).order_by('-initiated_at')[:limit]
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error searching consultations: {e}")
            return []
    
    def get_consultation_messages(self, consultation_id: ConsultationId) -> List[dict]:
        """Get all messages in a consultation"""
        try:
            model = ConsultationModel.objects.get(consultation_id=consultation_id.value)
            messages = ConsultationMessageModel.objects.filter(
                consultation=model
            ).order_by('created_at')
            
            return [
                {
                    'id': msg.message_id,
                    'type': msg.message_type,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat(),
                    'assessment': msg.ai_assessment_json
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}")
            return []
    
    def get_consultation_recommendations(self, consultation_id: ConsultationId) -> List[dict]:
        """Get all recommendations for a consultation"""
        try:
            model = ConsultationModel.objects.get(consultation_id=consultation_id.value)
            recommendations = ConsultationRecommendationModel.objects.filter(
                consultation=model
            ).order_by('-created_at')
            
            return [
                {
                    'id': rec.recommendation_id,
                    'type': rec.recommendation_type,
                    'title': rec.title,
                    'description': rec.description,
                    'medication': rec.medication_name,
                    'dosage': rec.dosage,
                    'frequency': rec.frequency,
                    'status': rec.status,
                    'confidence': rec.confidence_score,
                    'endorsed_at': rec.clinician_endorsed_at.isoformat() if rec.clinician_endorsed_at else None
                }
                for rec in recommendations
            ]
        except Exception as e:
            logger.error(f"Error retrieving recommendations: {e}")
            return []
    
    def add_message(self, consultation_id: ConsultationId, message_type: str,
                   content: str, assessment_json: Optional[dict] = None) -> str:
        """Add message to consultation"""
        try:
            import uuid
            model = ConsultationModel.objects.get(consultation_id=consultation_id.value)
            message_id = str(uuid.uuid4())
            
            ConsultationMessageModel.objects.create(
                message_id=message_id,
                consultation=model,
                message_type=message_type,
                content=content,
                ai_assessment_json=assessment_json or {}
            )
            
            logger.info(f"Message added: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise
    
    def add_recommendation(self, consultation_id: ConsultationId,
                         recommendation_type: str, title: str, description: str,
                         medication_name: Optional[str] = None,
                         dosage: Optional[str] = None,
                         frequency: Optional[str] = None,
                         confidence: float = 0.5) -> str:
        """Add recommendation to consultation"""
        try:
            import uuid
            model = ConsultationModel.objects.get(consultation_id=consultation_id.value)
            recommendation_id = str(uuid.uuid4())
            
            ConsultationRecommendationModel.objects.create(
                recommendation_id=recommendation_id,
                consultation=model,
                recommendation_type=recommendation_type,
                title=title,
                description=description,
                medication_name=medication_name,
                dosage=dosage,
                frequency=frequency,
                confidence_score=confidence
            )
            
            logger.info(f"Recommendation added: {recommendation_id}")
            return recommendation_id
        except Exception as e:
            logger.error(f"Error adding recommendation: {e}")
            raise
    
    def mark_recommendation_endorsed(self, recommendation_id: str,
                                    clinician_notes: str = "") -> bool:
        """Mark recommendation as endorsed by clinician"""
        try:
            rec = ConsultationRecommendationModel.objects.get(recommendation_id=recommendation_id)
            rec.status = 'ENDORSED'
            rec.clinician_notes = clinician_notes
            rec.clinician_endorsed_at = datetime.now()
            rec.save()
            
            logger.info(f"Recommendation endorsed: {recommendation_id}")
            return True
        except Exception as e:
            logger.error(f"Error endorsing recommendation: {e}")
            return False
    
    def mark_recommendation_rejected(self, recommendation_id: str,
                                    clinician_notes: str = "") -> bool:
        """Mark recommendation as rejected by clinician"""
        try:
            rec = ConsultationRecommendationModel.objects.get(recommendation_id=recommendation_id)
            rec.status = 'REJECTED'
            rec.clinician_notes = clinician_notes
            rec.save()
            
            logger.info(f"Recommendation rejected: {recommendation_id}")
            return True
        except Exception as e:
            logger.error(f"Error rejecting recommendation: {e}")
            return False
    
    def update_consultation_status(self, consultation_id: ConsultationId,
                                  new_status: str) -> bool:
        """Update consultation status"""
        try:
            model = ConsultationModel.objects.get(consultation_id=consultation_id.value)
            model.status = new_status
            
            if new_status == 'COMPLETED':
                model.completed_at = datetime.now()
            elif new_status == 'EXPIRED':
                model.expires_at = datetime.now()
            
            model.save()
            logger.info(f"Consultation status updated: {consultation_id.value} -> {new_status}")
            return True
        except Exception as e:
            logger.error(f"Error updating consultation status: {e}")
            return False
    
    def _model_to_entity(self, model: ConsultationModel) -> Consultation:
        """Convert ORM model to domain entity"""
        consultation = Consultation(
            consultation_id=ConsultationId(model.consultation_id),
            patient_id=PatientId(model.patient_id),
            chief_complaint=model.chief_complaint,
            medical_background=MedicalBackground(**model.medical_background_json),
            urgency_level=model.urgency_level
        )
        
        if model.activated_clinician_id:
            consultation.activated_clinician_id = ClinicianId(model.activated_clinician_id)
        
        consultation._status = model.status
        consultation._is_urgent_case = model.is_urgent_case
        consultation._red_flags_detected = model.red_flags_detected
        consultation.completed_at = model.completed_at
        consultation.expires_at = model.expires_at
        
        return consultation
    
    def _publish_domain_events(self, consultation: Consultation) -> None:
        """Extract and publish domain events from aggregate"""
        try:
            publisher = EventBusFactory.get_publisher()
            
            for event in consultation.domain_events:
                publisher.publish(event)
                logger.debug(f"Event published: {event.__class__.__name__}")
            
            # Clear events after publishing (event sourcing pattern)
            consultation.domain_events.clear()
            
        except Exception as e:
            logger.warning(f"Could not publish domain events: {e}")
