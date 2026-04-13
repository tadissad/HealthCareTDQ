"""
Dispensing Service - Event Listeners
Subscribes to pharmacy, prescription, and payment events
"""

import logging
from shared_ddd.event_bus import EventBusFactory

logger = logging.getLogger(__name__)


class DispensingEventListener:
    """Listen to dispensing-relevant domain events"""
    
    def __init__(self):
        try:
            self.subscriber = EventBusFactory.get_subscriber('dispensing_service')
        except Exception as e:
            logger.warning(f"Could not initialize subscriber: {e}")
            self.subscriber = None
    
    def subscribe_to_prescription_events(self):
        """Subscribe to prescription events"""
        if not self.subscriber:
            return
        
        # When prescription is confirmed, can start dispensing
        self.subscriber.subscribe(
            'PrescriptionConfirmed',
            self.on_prescription_confirmed
        )
        
        # When prescription expires, cancel related orders
        self.subscriber.subscribe(
            'PrescriptionExpired',
            self.on_prescription_expired
        )
    
    def subscribe_to_pharmacy_events(self):
        """Subscribe to pharmacy events"""
        if not self.subscriber:
            return
        
        # When inventory is low, may need to delay dispensing
        self.subscriber.subscribe(
            'InventoryLowAlert',
            self.on_inventory_low
        )
        
        # When product expires, cannot dispense
        self.subscriber.subscribe(
            'ProductExpiringAlert',
            self.on_product_expiring
        )
    
    def on_prescription_confirmed(self, event_data):
        """
        Handle prescription confirmed
        Can now create order and prepare for dispensing
        """
        prescription_id = event_data.get('prescription_id')
        logger.info(f"Prescription confirmed: {prescription_id}")
        
        # Logic:
        # 1. Create order from confirmed prescription
        # 2. Verify inventory availability
        # 3. Set order status to READY_FOR_DISPENSING
        # 4. Prepare picking slip for warehouse
    
    def on_prescription_expired(self, event_data):
        """
        Handle prescription expired
        Cancel related orders if not yet dispensed
        """
        prescription_id = event_data.get('prescription_id')
        logger.warning(f"Prescription expired: {prescription_id}")
        
        # Logic:
        # 1. Find orders for this prescription
        # 2. If order status is <= CONFIRMED, cancel it
        # 3. Release reserved inventory
        # 4. Notify patient about cancellation
    
    def on_inventory_low(self, event_data):
        """
        Handle inventory low alert
        May need to backorder items
        """
        product_id = event_data.get('product_id')
        current_qty = event_data.get('current_quantity')
        logger.warning(f"Inventory low: {product_id} (qty: {current_qty})")
        
        # Logic:
        # 1. Check pending orders with this product
        # 2. If quantity insufficient, notify customer
        # 3. Offer options: wait/substitute/cancel
    
    def on_product_expiring(self, event_data):
        """
        Handle product expiring alert
        Cannot dispense products about to expire
        """
        product_id = event_data.get('product_id')
        expiry_date = event_data.get('expiry_date')
        logger.warning(f"Product expiring: {product_id} on {expiry_date}")
        
        # Logic:
        # 1. Find orders waiting to dispense this product
        # 2. Cannot dispense if expiring within 30 days (configurable)
        # 3. Offer substitute product or refund
    
    def start_listening(self):
        """Start listening for events"""
        if not self.subscriber:
            logger.error("Subscriber not initialized")
            return
        
        self.subscribe_to_prescription_events()
        self.subscribe_to_pharmacy_events()
        
        logger.info("Dispensing service event listener started")


class DispensingEventPublisher:
    """Publish dispensing domain events"""
    
    def __init__(self):
        try:
            self.publisher = EventBusFactory.get_publisher()
        except Exception as e:
            logger.warning(f"Could not initialize publisher: {e}")
            self.publisher = None
    
    def publish_order_created(self, order_id, prescription_id, customer_id):
        """Publish order created event"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class OrderCreatedEvent(DomainEvent):
            order_id: str
            prescription_id: str
            customer_id: str
            event_type: str = "OrderCreated"
        
        event = OrderCreatedEvent(order_id, prescription_id, customer_id)
        self.publisher.publish(event)
        logger.info(f"Order created: {order_id}")
    
    def publish_order_confirmed(self, order_id):
        """Publish order confirmed event"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class OrderConfirmedEvent(DomainEvent):
            order_id: str
            event_type: str = "OrderConfirmed"
        
        event = OrderConfirmedEvent(order_id)
        self.publisher.publish(event)
    
    def publish_item_dispensed(self, order_id, product_id, quantity):
        """Publish item dispensed event"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class ItemDispensedEvent(DomainEvent):
            order_id: str
            product_id: str
            quantity: int
            event_type: str = "ItemDispensed"
        
        event = ItemDispensedEvent(order_id, product_id, quantity)
        self.publisher.publish(event)
    
    def publish_order_shipped(self, order_id, tracking_number, estimated_delivery):
        """Publish order shipped event"""
        if not self.publisher:
            return
        
        from dataclasses import dataclass
        from shared_ddd.base import DomainEvent
        
        @dataclass
        class OrderShippedEvent(DomainEvent):
            order_id: str
            tracking_number: str
            estimated_delivery: str
            event_type: str = "OrderShipped"
        
        event = OrderShippedEvent(order_id, tracking_number, estimated_delivery)
        self.publisher.publish(event)
