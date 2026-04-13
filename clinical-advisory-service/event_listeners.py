"""
Clinical-Advisory Service - Event Listeners
Subscribes to prescription, pharmacy, and dispensing events
"""

import logging
from shared_ddd.event_bus import EventBusFactory

logger = logging.getLogger(__name__)


class ClinicalAdvisoryEventListener:
    """Listen to clinical-advisory-relevant domain events"""
    
    def __init__(self):
        try:
            self.subscriber = EventBusFactory.get_subscriber('clinical_advisory_service')
        except Exception as e:
            logger.warning(f"Could not initialize subscriber: {e}")
            self.subscriber = None
    
    def subscribe_to_prescription_events(self):
        """Subscribe to prescription events"""
        if not self.subscriber:
            return
        
        # When prescription validation fails, may need clinical review
        self.subscriber.subscribe(
            'PrescriptionValidationFailed',
            self.on_prescription_validation_failed
        )
        
        # When prescription is submitted, can provide clinical guidance
        self.subscriber.subscribe(
            'PrescriptionSubmitted',
            self.on_prescription_submitted
        )
    
    def subscribe_to_dispensing_events(self):
        """Subscribe to dispensing events"""
        if not self.subscriber:
            return
        
        # When payment fails, may need to adjust recommendations
        self.subscriber.subscribe(
            'PaymentFailed',
            self.on_payment_failed
        )
        
        # When order is cancelled, close related consultation
        self.subscriber.subscribe(
            'OrderCancelled',
            self.on_order_cancelled
        )
    
    def subscribe_to_urgent_alerts(self):
        """Subscribe to urgent medical cases"""
        if not self.subscriber:
            return
        
        # When prescription validation detects urgent case
        self.subscriber.subscribe(
            'UrgentCaseDetected',
            self.on_urgent_case_detected
        )
    
    def on_prescription_validation_failed(self, event_data):
        """
        Handle prescription validation failure
        May require clinical re-review
        """
        prescription_id = event_data.get('prescription_id')
        reason = event_data.get('reason', 'Unknown')
        logger.warning(f"Prescription validation failed: {prescription_id} - {reason}")
        
        # Logic:
        # 1. Find related consultation
        # 2. Mark as requiring clinician review
        # 3. Notify clinician or AI system
        # 4. Suggest alternative recommendations
    
    def on_prescription_submitted(self, event_data):
        """
        Handle prescription submitted
        Provide clinical guidance and recommendations
        """
        prescription_id = event_data.get('prescription_id')
        logger.info(f"Prescription submitted: {prescription_id}")
        
        # Logic:
        # 1. Retrieve consultation for this prescription
        # 2. Generate clinical recommendations
        # 3. Check for drug interactions
        # 4. Verify dosage appropriateness
        # 5. Send recommendations back to prescription service
    
    def on_payment_failed(self, event_data):
        """
        Handle payment failure
        Offer alternative treatments or generics
        """
        order_id = event_data.get('order_id')
        logger.warning(f"Payment failed: {order_id}")
        
        # Logic:
        # 1. Find related prescription/consultation
        # 2. Offer lower-cost alternatives
        # 3. Suggest generic medications
        # 4. Check insurance coverage
    
    def on_order_cancelled(self, event_data):
        """
        Handle order cancelled
        Close or suspend related consultation
        """
        order_id = event_data.get('order_id')
        logger.info(f"Order cancelled: {order_id}")
        
        # Logic:
        # 1. Find related consultation
        # 2. Update consultation status to CANCELLED
        # 3. Archive recommendations
        # 4. Notify patient about alternative care options
    
    def on_urgent_case_detected(self, event_data):
        """
        Handle urgent case detected
        Escalate to emergency protocols
        """
        indicators = event_data.get('urgency_indicators', [])
        logger.error(f"URGENT CASE: {indicators}")
        
        # Logic:
        # 1. Create emergency consultation
        # 2. Immediately alert available clinicians
        # 3. Recommend emergency room visit
        # 4. Send incident to hospital if needed
    
    def start_listening(self):
        """Start listening for events"""
        if not self.subscriber:
            logger.error("Subscriber not initialized")
            return
        
        self.subscribe_to_prescription_events()
        self.subscribe_to_dispensing_events()
        self.subscribe_to_urgent_alerts()
        
        logger.info("Clinical-Advisory service event listener started")


class ClinicalAdvisoryEventPublisher:
    """Publish clinical-advisory domain events"""
    
    def __init__(self):
        try:
            self.publisher = EventBusFactory.get_publisher()
        except Exception as e:
            logger.warning(f"Could not initialize publisher: {e}")
            self.publisher = None
    
    def publish_consultation_completed(self, consultation_id, recommendation_count):
        """Publish consultation completed event"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class ConsultationCompletedEvent(DomainEvent):
            consultation_id: str
            recommendation_count: int
            event_type: str = "ConsultationCompleted"
        
        event = ConsultationCompletedEvent(consultation_id, recommendation_count)
        self.publisher.publish(event)
        logger.info(f"Consultation completed: {consultation_id}")
    
    def publish_urgent_case_detected(self, consultation_id, indicators, recommended_action):
        """Publish urgent case detected event"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class ClinicalUrgentCaseEvent(DomainEvent):
            consultation_id: str
            indicators: list
            recommended_action: str
            event_type: str = "ClinicalUrgentCaseDetected"
        
        event = ClinicalUrgentCaseEvent(consultation_id, indicators, recommended_action)
        self.publisher.publish(event)
        logger.error(f"Urgent case published: {consultation_id}")
    
    def publish_drug_interaction_warning(self, consultation_id, drug1, drug2, severity):
        """Publish drug interaction warning"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class DrugInteractionWarning(DomainEvent):
            consultation_id: str
            drug1: str
            drug2: str
            severity: str
            event_type: str = "DrugInteractionWarning"
        
        event = DrugInteractionWarning(consultation_id, drug1, drug2, severity)
        self.publisher.publish(event)
        logger.warning(f"Drug interaction warning: {drug1} + {drug2}")
    
    def publish_dosage_recommendation(self, consultation_id, medication, dosage, frequency):
        """Publish dosage recommendation"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class DosageRecommendationEvent(DomainEvent):
            consultation_id: str
            medication: str
            dosage: str
            frequency: str
            event_type: str = "DosageRecommendation"
        
        event = DosageRecommendationEvent(consultation_id, medication, dosage, frequency)
        self.publisher.publish(event)
