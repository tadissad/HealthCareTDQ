"""
Base classes for DDD implementation across all services
This module should be copied/reused in each service's domain/ folder
"""

from typing import Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod


# ============================================================================
# VALUE OBJECTS
# ============================================================================

class ValueObject(ABC):
    """
    Base class for Value Objects
    - No identity (defined by their attributes)
    - Immutable
    - Inter-changeable if attributes are equal
    """
    
    @abstractmethod
    def equals(self, other: "ValueObject") -> bool:
        """Compare two value objects by their attributes"""
        pass
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.equals(other)
    
    def __ne__(self, other):
        return not self.__eq__(other)


# ============================================================================
# ENTITIES
# ============================================================================

class Entity:
    """
    Base class for Entities
    - Have unique identity
    - Can change attributes
    - Equality is based on ID only
    """
    
    def __init__(self, id: Any):
        self.id = id
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash(self.id)


# ============================================================================
# AGGREGATES
# ============================================================================

class Aggregate(Entity):
    """
    Base class for Aggregate Roots
    - An entity that is the root of an aggregate
    - Contains other entities and value objects
    - Can raise domain events
    """
    
    def __init__(self, id: Any):
        super().__init__(id)
        self._events: List["DomainEvent"] = []
    
    def add_event(self, event: "DomainEvent") -> None:
        """Add a domain event to be published"""
        self._events.append(event)
    
    def get_events(self) -> List["DomainEvent"]:
        """Get all pending domain events"""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear all pending events (call after publishing)"""
        self._events.clear()


# ============================================================================
# DOMAIN EVENTS
# ============================================================================

@dataclass
class DomainEvent:
    """
    Base class for Domain Events
    - Represent something that happened in the domain
    - Should be immutable
    - Contains aggregate_id so subscribers know which aggregate changed
    """
    aggregate_id: Any
    event_type: str
    occurred_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.occurred_at is None:
            self.occurred_at = datetime.now()


class DomainEventPublisher:
    """
    Publisher for domain events
    In-memory implementation (can be replaced with RabbitMQ/Redis later)
    """
    _handlers = {}
    
    @classmethod
    def subscribe(cls, event_type: str, handler):
        """Subscribe to an event type"""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
    
    @classmethod
    def publish(cls, event: DomainEvent) -> None:
        """Publish an event to all subscribers"""
        event_type = event.__class__.__name__
        if event_type in cls._handlers:
            for handler in cls._handlers[event_type]:
                handler(event)
    
    @classmethod
    def clear(cls):
        """Clear all subscriptions (for testing)"""
        cls._handlers.clear()


# ============================================================================
# REPOSITORIES
# ============================================================================

class IRepository(ABC):
    """
    Interface for repositories
    - Define contract for persistence without implementation details
    - Implementation can use any persistence mechanism (SQL, NoSQL, etc.)
    """
    
    @abstractmethod
    def add(self, aggregate: Aggregate) -> None:
        """Add a new aggregate to the repository"""
        pass
    
    @abstractmethod
    def update(self, aggregate: Aggregate) -> None:
        """Update an existing aggregate"""
        pass
    
    @abstractmethod
    def remove(self, aggregate: Aggregate) -> None:
        """Remove an aggregate from the repository"""
        pass
    
    @abstractmethod
    def get_by_id(self, id: Any) -> Optional[Aggregate]:
        """Get aggregate by ID"""
        pass


# ============================================================================
# DOMAIN SERVICES
# ============================================================================

class DomainService(ABC):
    """
    Base class for Domain Services
    - Contain complex business logic that doesn't belong to single entities
    - Stateless operations
    - Should NOT be confused with Application Services
    """
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the domain service logic"""
        pass


# ============================================================================
# APPLICATION EXCEPTIONS
# ============================================================================

class DomainException(Exception):
    """Base exception for domain-specific errors"""
    pass


class AggregateNotFoundException(DomainException):
    """Raise when an aggregate is not found"""
    
    def __init__(self, aggregate_type: str, id: Any):
        super().__init__(f"{aggregate_type} with ID {id} not found")


class InvalidValueObjectException(DomainException):
    """Raise when creating an invalid value object"""
    pass


class InvalidAggregateStateException(DomainException):
    """Raise when an aggregate is in invalid state for an operation"""
    pass
