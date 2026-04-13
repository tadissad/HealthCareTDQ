"""
Event Bus Integration - Updated Repository Base with Event Publishing
"""

import logging
from typing import Optional, List
from shared_ddd.base import Aggregate
from shared_ddd.event_bus import IEventPublisher, EventBusFactory

logger = logging.getLogger(__name__)


class RepositoryWithEventPublishing:
    """
    Base repository that publishes domain events to event bus
    All concrete repositories should inherit this pattern
    """
    
    def __init__(self, event_publisher: Optional[IEventPublisher] = None):
        """
        Initialize repository with optional event publisher
        If not provided, uses default from EventBusFactory
        """
        self.event_publisher = event_publisher or self._get_default_publisher()
    
    def _get_default_publisher(self) -> IEventPublisher:
        """Get default event publisher from factory"""
        try:
            return EventBusFactory.get_publisher()
        except Exception as e:
            logger.warning(f"Could not initialize event bus: {e}. Events won't be published.")
            return None
    
    def _publish_events(self, aggregate: Aggregate) -> None:
        """
        Publish all domain events from aggregate
        Called after persisting aggregate
        """
        if not self.event_publisher:
            return
        
        try:
            events = aggregate.get_events()
            for event in events:
                self.event_publisher.publish(event)
            
            # Clear events after publishing
            aggregate.clear_events()
            logger.debug(f"Published {len(events)} events")
        except Exception as e:
            logger.error(f"Error publishing events: {e}")
            # Don't fail transaction if event publishing fails
            # Events can be retried later via event store


# ============================================================================
# Example Integration Pattern for Each Service Repository
# ============================================================================

class EnhancedPrescriptionRepository:
    """
    Example of how to integrate event bus with prescription repository
    Pattern to follow for all services
    """
    
    def __init__(self, event_publisher: Optional[IEventPublisher] = None):
        self.event_publisher = event_publisher or self._get_default_publisher()
    
    def _get_default_publisher(self) -> IEventPublisher:
        """Get event publisher"""
        try:
            return EventBusFactory.get_publisher()
        except Exception as e:
            logger.warning(f"Event bus unavailable: {e}")
            return None
    
    def add(self, prescription) -> None:
        """Add prescription and publish events"""
        # ... existing persistence logic ...
        self._publish_events(prescription)
    
    def update(self, prescription) -> None:
        """Update prescription and publish events"""
        # ... existing persistence logic ...
        self._publish_events(prescription)
    
    def _publish_events(self, aggregate) -> None:
        """Publish domain events"""
        if not self.event_publisher:
            return
        
        try:
            events = aggregate.get_events()
            for event in events:
                # Determine routing key based on event type
                routing_key = event.__class__.__name__
                self.event_publisher.publish(event, routing_key)
            
            aggregate.clear_events()
            logger.info(f"Published {len(events)} events for {aggregate.prescription_id.value}")
        except Exception as e:
            logger.error(f"Failed to publish events: {e}")
