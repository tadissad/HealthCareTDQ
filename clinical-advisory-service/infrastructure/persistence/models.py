"""
Clinical-Advisory Service - Infrastructure Layer - Models
Django ORM models for Consultation, Message, Recommendation, and Domain Events
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
import json


class ConsultationModel(models.Model):
    """ORM Model for Consultation aggregate"""
    
    CONSULTATION_STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('AWAITING_CLINICIAN', 'Awaiting Clinician'),
        ('IN_PROGRESS', 'In Progress'),
        ('RECOMMENDATION_PENDING', 'Recommendation Pending'),
        ('RECOMMENDATION_READY', 'Recommendation Ready'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    URGENCY_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Identifiers
    consultation_id = models.CharField(
        max_length=36,
        unique=True,
        db_index=True,
        help_text="UUID for consultation"
    )
    patient_id = models.CharField(
        max_length=36,
        db_index=True,
        help_text="Reference to Patient service"
    )
    activated_clinician_id = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        help_text="Assigned clinician, if any"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=25,
        choices=CONSULTATION_STATUS_CHOICES,
        default='INITIATED',
        db_index=True
    )
    urgency_level = models.CharField(
        max_length=15,
        choices=URGENCY_LEVEL_CHOICES,
        default='LOW',
        db_index=True
    )
    
    # Medical background
    chief_complaint = models.TextField(
        help_text="Primary reason for consultation"
    )
    medical_background_json = models.JSONField(
        default=dict,
        help_text="Medical history, allergies, current medications"
    )
    
    # Emergency flags
    is_urgent_case = models.BooleanField(
        default=False,
        db_index=True
    )
    red_flags_detected = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Emergency indicators found"
    )
    
    # Message tracking
    patient_message_count = models.IntegerField(default=0)
    ai_message_count = models.IntegerField(default=0)
    clinician_message_count = models.IntegerField(default=0)
    
    # Recommendation tracking
    ai_recommendation_count = models.IntegerField(default=0)
    endorsed_recommendations_count = models.IntegerField(default=0)
    rejected_recommendations_count = models.IntegerField(default=0)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Domain event tracking
    domain_events_json = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'clinical_consultations'
        indexes = [
            models.Index(fields=['patient_id', '-initiated_at']),
            models.Index(fields=['status', 'urgency_level']),
            models.Index(fields=['is_urgent_case', '-initiated_at']),
        ]
    
    def to_entity(self):
        """Convert ORM model to domain entity"""
        from clinical_advisory_service.domain.entities import Consultation
        from clinical_advisory_service.domain.value_objects import (
            ConsultationId, PatientId, ClinicianId, MedicalBackground
        )
        
        consultation = Consultation(
            consultation_id=ConsultationId(self.consultation_id),
            patient_id=PatientId(self.patient_id),
            chief_complaint=self.chief_complaint,
            medical_background=MedicalBackground(**self.medical_background_json),
            urgency_level=self.urgency_level,
        )
        
        if self.activated_clinician_id:
            consultation.activated_clinician_id = ClinicianId(self.activated_clinician_id)
        
        consultation._status = self.status
        consultation._is_urgent_case = self.is_urgent_case
        consultation._red_flags_detected = self.red_flags_detected
        
        return consultation


class ConsultationMessageModel(models.Model):
    """ORM Model for consultation messages"""
    
    MESSAGE_TYPE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('AI', 'AI Screening'),
        ('CLINICIAN', 'Clinician'),
        ('SYSTEM', 'System'),
    ]
    
    message_id = models.CharField(max_length=36, unique=True, db_index=True)
    consultation = models.ForeignKey(
        ConsultationModel,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    message_type = models.CharField(
        max_length=15,
        choices=MESSAGE_TYPE_CHOICES,
        db_index=True
    )
    content = models.TextField()
    
    # For AI messages: screening results
    ai_assessment_json = models.JSONField(null=True, blank=True)
    
    # Timeline
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'consultation_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['consultation', 'created_at']),
            models.Index(fields=['message_type', 'created_at']),
        ]


class ConsultationRecommendationModel(models.Model):
    """ORM Model for clinical recommendations"""
    
    RECOMMENDATION_TYPE_CHOICES = [
        ('SELF_CARE', 'Self Care'),
        ('OTC_MEDICATION', 'Over-The-Counter Medicine'),
        ('SPECIALIST_REFERRAL', 'Specialist Referral'),
        ('URGENT_CARE', 'Urgent Care'),
        ('EDUCATIONAL', 'Educational'),
        ('PRESCRIPTION_NEEDED', 'Prescription Needed'),
    ]
    
    STATUS_CHOICES = [
        ('GENERATED', 'Generated'),
        ('ENDORSED', 'Endorsed'),
        ('REJECTED', 'Rejected'),
        ('IMPLEMENTED', 'Implemented'),
        ('EXPIRED', 'Expired'),
    ]
    
    recommendation_id = models.CharField(max_length=36, unique=True, db_index=True)
    consultation = models.ForeignKey(
        ConsultationModel,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPE_CHOICES,
        db_index=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # For medication recommendations
    medication_name = models.CharField(max_length=255, null=True, blank=True)
    dosage = models.CharField(max_length=100, null=True, blank=True)
    frequency = models.CharField(max_length=100, null=True, blank=True)
    duration_days = models.IntegerField(null=True, blank=True)
    
    # Clinician validation
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='GENERATED',
        db_index=True
    )
    clinician_notes = models.TextField(null=True, blank=True)
    clinician_endorsed_at = models.DateTimeField(null=True, blank=True)
    
    # Evidence/confidence
    confidence_score = models.FloatField(default=0.5)  # 0.0 to 1.0
    supporting_evidence_json = models.JSONField(default=list, blank=True)
    
    # Timeline
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'consultation_recommendations'
        indexes = [
            models.Index(fields=['consultation', 'status']),
            models.Index(fields=['recommendation_type', 'created_at']),
        ]


class DomainEventModel(models.Model):
    """Store domain events for audit trail and event sourcing"""
    
    event_type = models.CharField(max_length=100, db_index=True)
    aggregate_id = models.CharField(max_length=36, db_index=True)
    aggregate_type = models.CharField(max_length=50)
    
    # Event data
    event_data_json = models.JSONField()
    
    # Metadata
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    # Publishing tracking
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'domain_events'
        ordering = ['occurred_at']
        indexes = [
            models.Index(fields=['aggregate_id', 'event_type']),
            models.Index(fields=['event_type', 'occurred_at']),
            models.Index(fields=['is_published', 'occurred_at']),
        ]
