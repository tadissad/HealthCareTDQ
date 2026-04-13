"""
Prescription Service - Event Listeners
Subscribes to events from other services
"""

import logging
from shared_ddd.event_bus import EventBusFactory

logger = logging.getLogger(__name__)


class PrescriptionEventListener:
    """Listen to prescription domain events"""
    
    def __init__(self):
        try:
            self.subscriber = EventBusFactory.get_subscriber('prescription_service')
        except Exception as e:
            logger.warning(f"Could not initialize subscriber: {e}")
            self.subscriber = None
    
    def subscribe_to_inventory_events(self):
        """Subscribe to pharmacy inventory events"""
        if not self.subscriber:
            return
        
        # When pharmacy updates product inventory, update prescriptions
        self.subscriber.subscribe(
            'ProductInventoryAdjusted',
            self.on_product_inventory_adjusted
        )
        
        # When product expires, mark prescriptions as requiring review
        self.subscriber.subscribe(
            'ProductExpired',
            self.on_product_expired
        )
    
    def subscribe_to_dispensing_events(self):
        """Subscribe to dispensing events"""
        if not self.subscriber:
            return
        
        # When dispensing completes, mark prescription as fulfilled
        self.subscriber.subscribe(
            'OrderFullyDispensed',
            self.on_order_fully_dispensed
        )
        
        # When payment fails, keep prescription in CONFIRMED state
        self.subscriber.subscribe(
            'PaymentFailed',
            self.on_payment_failed
        )
    
    def on_product_inventory_adjusted(self, event_data):
        """Handle pharmacy inventory adjustment"""
        logger.info(f"Product inventory adjusted: {event_data}")
        # Logic: Check if any pending prescriptions have this product
        # Update availability status
    
    def on_product_expired(self, event_data):
        """Handle product expiration"""
        product_id = event_data.get('product_id')
        logger.warning(f"Product expired: {product_id}")
        # Logic: Find prescriptions containing expired product
        # Flag for clinician review
    
    def on_order_fully_dispensed(self, event_data):
        """Handle order fully dispensed"""
        order_id = event_data.get('order_id')
        logger.info(f"Order fully dispensed: {order_id}")
        # Logic: Find corresponding prescription
        # Update status to FULFILLED
    
    def on_payment_failed(self, event_data):
        """Handle payment failure"""
        order_id = event_data.get('order_id')
        logger.error(f"Payment failed for order: {order_id}")
        # Logic: Prescription stays in CONFIRMED
        # Notify patient to retry payment
    
    def start_listening(self):
        """Start listening for all events"""
        if not self.subscriber:
            logger.error("Subscriber not initialized")
            return
        
        self.subscribe_to_inventory_events()
        self.subscribe_to_dispensing_events()
        
        logger.info("Prescription service event listener started")
        # Note: This runs in background thread/process
        # self.subscriber.start_listening()


class PrescriptionEventPublisher:
    """Publish prescription domain events"""
    
    def __init__(self):
        try:
            self.publisher = EventBusFactory.get_publisher()
        except Exception as e:
            logger.warning(f"Could not initialize publisher: {e}")
            self.publisher = None
    
    def publish_prescription_created(self, prescription_id, patient_id):
        """Publish prescription created event"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class PrescriptionCreatedEvent(DomainEvent):
            prescription_id: str
            patient_id: str
            event_type: str = "PrescriptionCreated"
        
        event = PrescriptionCreatedEvent(prescription_id, patient_id)
        self.publisher.publish(event)
    
    def publish_prescription_submitted(self, prescription_id):
        """Publish prescription submitted event"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class PrescriptionSubmittedEvent(DomainEvent):
            prescription_id: str
            event_type: str = "PrescriptionSubmitted"
        
        event = PrescriptionSubmittedEvent(prescription_id)
        self.publisher.publish(event)
    
    def publish_prescription_confirmed(self, prescription_id):
        """Publish prescription confirmed event"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class PrescriptionConfirmedEvent(DomainEvent):
            prescription_id: str
            event_type: str = "PrescriptionConfirmed"
        
        event = PrescriptionConfirmedEvent(prescription_id)
        self.publisher.publish(event)
