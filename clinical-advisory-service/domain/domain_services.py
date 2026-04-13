"""
Clinical-Advisory Service Domain Layer - Domain Services
"""

from typing import List, Optional
from datetime import datetime

from shared_ddd.base import DomainService

from .value_objects import (
    ConsultationId, PatientId, ClinicianId, Symptom, SymptomProfile,
    MedicalBackground, MedicalRecommendation, RecommendationType
)
from .entities import Consultation, ConversationThread
from .repositories import IClinicalConsultationRepository


class ConsultationInitializationService(DomainService):
    """Service for initializing new consultations"""
    
    def create_consultation(
        self,
        patient_id: PatientId,
        chief_complaint: str,
        symptoms: List[Symptom],
        medical_background: MedicalBackground
    ) -> Consultation:
        """Create new consultation with initial data"""
        
        # Validate inputs
        if not chief_complaint or len(chief_complaint.strip()) < 1:
            raise ValueError("Chief complaint is required")
        if len(symptoms) == 0:
            raise ValueError("At least one symptom must be provided")
        
        # Create symptom profile
        symptom_profile = SymptomProfile(
            symptoms=symptoms,
            chief_complaint=chief_complaint
        )
        
        # Create consultation aggregate
        consultation = Consultation(
            consultation_id=ConsultationId(),
            patient_id=patient_id,
            medical_background=medical_background,
            symptom_profile=symptom_profile,
            conversation=ConversationThread(),
            status=None,  # Will be set in entity __post_init__
            initiated_at=datetime.now()
        )
        
        return consultation


class AIScreeningService(DomainService):
    """Service for AI-based initial symptom screening"""
    
    def perform_initial_screening(self, consultation: Consultation) -> str:
        """Perform AI screening and return screening summary"""
        
        # In real implementation, would call Gemini API or local model
        # For now, return structured screening summary
        
        symptoms_text = ", ".join([
            f"{s.symptom_name} (severity {s.severity}/10, duration: {s.duration})"
            for s in consultation.symptom_profile.symptoms
        ])
        
        screening_summary = f"""
        Initial AI Screening:
        - Chief Complaint: {consultation.symptom_profile.chief_complaint}
        - Current Symptoms: {symptoms_text}
        - Age: {consultation.medical_background.age}
        - Chronic Conditions: {', '.join(consultation.medical_background.chronic_conditions) or 'None'}
        - Allergies: {', '.join(consultation.medical_background.allergies) or 'None'}
        
        This is an AI pre-screening. Consultation awaiting clinician review.
        """
        
        # Add AI screening message to conversation
        consultation.add_ai_message(
            content=screening_summary,
            sender_name="AI Assistant"
        )
        
        return screening_summary


class RecommendationGenerationService(DomainService):
    """Service for generating medical recommendations"""
    
    def generate_self_care_recommendation(
        self,
        title: str,
        description: str,
        contraindications: List[str] = None,
        confidence_score: float = 0.85
    ) -> MedicalRecommendation:
        """Generate self-care recommendation"""
        return MedicalRecommendation(
            recommendation_type=RecommendationType.SELF_CARE,
            title=title,
            description=description,
            contraindications=contraindications or [],
            confidence_score=confidence_score
        )
    
    def generate_otc_medication_recommendation(
        self,
        medication_name: str,
        dosage: str,
        frequency: str,
        duration: str,
        contraindications: List[str] = None,
        confidence_score: float = 0.80
    ) -> MedicalRecommendation:
        """Generate OTC medication recommendation"""
        description = f"""
        Medication: {medication_name}
        Dosage: {dosage}
        Frequency: {frequency}
        Duration: {duration}
        """
        return MedicalRecommendation(
            recommendation_type=RecommendationType.OTC_MEDICATION,
            title=f"{medication_name} for symptomatic relief",
            description=description,
            contraindications=contraindications or [],
            confidence_score=confidence_score
        )
    
    def generate_specialist_referral(
        self,
        specialist_type: str,
        reason: str,
        urgency: str = "routine",
        confidence_score: float = 0.90
    ) -> MedicalRecommendation:
        """Generate specialist referral recommendation"""
        return MedicalRecommendation(
            recommendation_type=RecommendationType.SPECIALIST_REFERRAL,
            title=f"Refer to {specialist_type}",
            description=f"Reason: {reason}. Urgency: {urgency}",
            confidence_score=confidence_score
        )
    
    def generate_urgent_care_recommendation(
        self,
        reason: str,
        instructions: str
    ) -> MedicalRecommendation:
        """Generate urgent care recommendation"""
        return MedicalRecommendation(
            recommendation_type=RecommendationType.URGENT_CARE,
            title="URGENT: Seek immediate medical attention",
            description=f"{reason}. Instructions: {instructions}",
            confidence_score=0.95,
            clinician_endorsed=False  # Definitely needs review
        )
    
    def generate_educational_recommendation(
        self,
        topic: str,
        content: str,
        confidence_score: float = 0.85
    ) -> MedicalRecommendation:
        """Generate educational/informational recommendation"""
        return MedicalRecommendation(
            recommendation_type=RecommendationType.CONDITION_INFO,
            title=f"Information about {topic}",
            description=content,
            confidence_score=confidence_score
        )


class UrgencyScoringService(DomainService):
    """Service for assessing clinical urgency"""
    
    RED_FLAG_SYMPTOMS = {
        "chest pain": 10,
        "difficulty breathing": 10,
        "unconsciousness": 10,
        "severe bleeding": 10,
        "high fever": 8,
        "sudden severe headache": 8,
        "paralysis": 10,
        "confusion": 8,
        "severe abdominal pain": 8,
        "uncontrolled vomiting": 7,
        "severe allergic reaction": 10,
    }
    
    def assess_urgency_level(self, consultation: Consultation) -> tuple[str, str]:
        """
        Assess urgency level and return (urgency_level, recommended_action)
        urgency_level: "low", "medium", "high", "urgent"
        recommended_action: "self_care", "urgent_care", "emergency_room", "call_ambulance"
        """
        urgency_score = 0
        detected_flags = []
        
        # Score symptoms
        for symptom in consultation.symptom_profile.symptoms:
            symptom_lower = symptom.symptom_name.lower()
            if symptom_lower in self.RED_FLAG_SYMPTOMS:
                score = self.RED_FLAG_SYMPTOMS[symptom_lower]
                urgency_score += score
                detected_flags.append(symptom.symptom_name)
            else:
                # General severity scoring
                urgency_score += symptom.severity
        
        # Age adjustment (very young or very old = higher urgency)
        age = consultation.medical_background.age
        if age < 5 or age > 75:
            urgency_score += 5
        
        # Chronic conditions increase urgency
        urgency_score += len(consultation.medical_background.chronic_conditions) * 3
        
        # Determine urgency level and action
        if urgency_score >= 18:
            return "urgent", "call_ambulance", detected_flags
        elif urgency_score >= 12:
            return "high", "emergency_room", detected_flags
        elif urgency_score >= 7:
            return "medium", "urgent_care", detected_flags
        else:
            return "low", "self_care", []
    
    def detect_red_flags(self, consultation: Consultation) -> List[str]:
        """Detect red flag symptoms requiring immediate attention"""
        red_flags = []
        for symptom in consultation.symptom_profile.symptoms:
            if symptom.symptom_name.lower() in self.RED_FLAG_SYMPTOMS:
                red_flags.append(symptom.symptom_name)
        return red_flags
