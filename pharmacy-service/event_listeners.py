"""
Pharmacy Service - Event Listeners
Subscribes to prescription and dispensing events
"""

import logging
from shared_ddd.event_bus import EventBusFactory

logger = logging.getLogger(__name__)


class PharmacyEventListener:
    """Listen to pharmacy-relevant domain events"""
    
    def __init__(self):
        try:
            self.subscriber = EventBusFactory.get_subscriber('pharmacy_service')
        except Exception as e:
            logger.warning(f"Could not initialize subscriber: {e}")
            self.subscriber = None
    
    def subscribe_to_prescription_events(self):
        """Subscribe to prescription events"""
        if not self.subscriber:
            return
        
        # When prescription is submitted, check inventory availability
        self.subscriber.subscribe(
            'PrescriptionSubmitted',
            self.on_prescription_submitted
        )
        
        # When prescription is confirmed, reserve inventory
        self.subscriber.subscribe(
            'PrescriptionConfirmed',
            self.on_prescription_confirmed
        )
    
    def subscribe_to_dispensing_events(self):
        """Subscribe to dispensing events"""
        if not self.subscriber:
            return
        
        # When order product is dispensed, adjust inventory
        self.subscriber.subscribe(
            'ItemDispensed',
            self.on_item_dispensed
        )
        
        # When order is cancelled, release inventory reservation
        self.subscriber.subscribe(
            'OrderCancelled',
            self.on_order_cancelled
        )
    
    def on_prescription_submitted(self, event_data):
        """
        Handle prescription submitted
        Check if pharmacy has required medicines in stock
        """
        prescription_id = event_data.get('prescription_id')
        logger.info(f"Prescription submitted: {prescription_id}")
        
        # Logic:
        # 1. Get prescription details from prescription_service
        # 2. Check inventory for each item
        # 3. Notify if out of stock
        # 4. Send availability report back to prescription service
    
    def on_prescription_confirmed(self, event_data):
        """
        Handle prescription confirmed
        Reserve inventory for this prescription
        """
        prescription_id = event_data.get('prescription_id')
        logger.info(f"Prescription confirmed: {prescription_id}")
        
        # Logic:
        # 1. Get prescription line items
        # 2. Reserve inventory (decrement available count)
        # 3. Create reservation record
        # 4. Notify patient that items are reserved
    
    def on_item_dispensed(self, event_data):
        """
        Handle item dispensed from order
        Update pharmacy inventory
        """
        product_id = event_data.get('product_id')
        quantity = event_data.get('quantity')
        logger.info(f"Item dispensed: {product_id}, qty: {quantity}")
        
        # Logic:
        # 1. Update FIFO batch management
        # 2. Remove from first available batch
        # 3. Update inventory totals
        # 4. Check if level is below minimum threshold
        # 5. Generate low stock alert if needed
    
    def on_order_cancelled(self, event_data):
        """
        Handle order cancelled
        Release reserved inventory
        """
        order_id = event_data.get('order_id')
        logger.info(f"Order cancelled: {order_id}")
        
        # Logic:
        # 1. Find inventory reservations for this order
        # 2. Release reserved quantities
        # 3. Return inventory to available pool
        # 4. Notify patient of cancellation
    
    def start_listening(self):
        """Start listening for events"""
        if not self.subscriber:
            logger.error("Subscriber not initialized")
            return
        
        self.subscribe_to_prescription_events()
        self.subscribe_to_dispensing_events()
        
        logger.info("Pharmacy service event listener started")


class PharmacyEventPublisher:
    """Publish pharmacy domain events"""
    
    def __init__(self):
        try:
            self.publisher = EventBusFactory.get_publisher()
        except Exception as e:
            logger.warning(f"Could not initialize publisher: {e}")
            self.publisher = None
    
    def publish_inventory_low(self, product_id, current_quantity, min_threshold):
        """Publish inventory low alert"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class InventoryLowAlert(DomainEvent):
            product_id: str
            current_quantity: int
            min_threshold: int
            event_type: str = "InventoryLowAlert"
        
        event = InventoryLowAlert(product_id, current_quantity, min_threshold)
        self.publisher.publish(event)
        logger.warning(f"Inventory low alert: {product_id}")
    
    def publish_product_expiring(self, product_id, batch_number, expiry_date):
        """Publish product expiring alert"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        from datetime import datetime
        
        @dataclass
        class ProductExpiringAlert(DomainEvent):
            product_id: str
            batch_number: str
            expiry_date: str
            event_type: str = "ProductExpiringAlert"
        
        event = ProductExpiringAlert(
            product_id,
            batch_number,
            expiry_date.isoformat() if isinstance(expiry_date, datetime) else str(expiry_date)
        )
        self.publisher.publish(event)
    
    def publish_inventory_adjusted(self, product_id, quantity_change, reason):
        """Publish inventory adjustment"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class InventoryAdjusted(DomainEvent):
            product_id: str
            quantity_change: int
            reason: str
            event_type: str = "InventoryAdjusted"
        
        event = InventoryAdjusted(product_id, quantity_change, reason)
        self.publisher.publish(event)
